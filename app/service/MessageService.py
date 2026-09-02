from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.common.Result import Result
from app.models.GitHubUser import GitHubUser
from app.models.Message import Message
from app.schemas.GitHubAuthSchemas import GitHubUserResponse
from app.schemas.MessageSchemas import (
    CreateMessageRequest,
    MessageCountResponse,
    MessageResponse,
    UpdateMessageStatusRequest,
)

_ALLOWED_MESSAGE_STATUS = {"pending", "approved", "rejected"}


def list_messages(session: Session, page: int = 1, size: int = 20) -> Result:
    """前台留言列表：已审核顶层分页，带嵌套 replies。

    只返回 status=approved。顶层按 created_at 降序；回复升序。
    size=1 时只返回 1 条顶层，其 replies 仍完整。

    Args:
        session: 数据库会话，由路由传入。
        page: 页码，从 1 开始。
        size: 每页顶层条数。

    Returns:
        统一结果集。成功时 code=200，data 为顶层留言列表。
    """
    # 1.查已审核顶层并分页（新的在前）
    root_rows = list(
        session.exec(
            select(Message)
            .where(Message.parent_id.is_(None), Message.status == "approved")
            .order_by(Message.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )

    # 2.BFS 拉齐本页顶层下已审核子孙
    all_rows = list(root_rows)
    frontier = [row.id for row in root_rows]
    while frontier:
        children = list(
            session.exec(
                select(Message).where(
                    Message.parent_id.in_(frontier), Message.status == "approved"
                )
            ).all()
        )
        all_rows.extend(children)
        frontier = [child.id for child in children]

    # 3.批量取留言者
    user_ids = {
        row.github_user_id for row in all_rows if row.github_user_id is not None
    }
    users_by_id: dict[int, GitHubUser] = {}
    if user_ids:
        for user in session.exec(
            select(GitHubUser).where(GitHubUser.id.in_(user_ids))
        ).all():
            users_by_id[user.id] = user

    # 4.建成 id → MessageResponse
    nodes: dict[int, MessageResponse] = {}
    for row in all_rows:
        github_user = None
        if row.github_user_id is not None:
            user = users_by_id.get(row.github_user_id)
            if user:
                github_user = GitHubUserResponse(
                    id=user.id,
                    login=user.login,
                    avatar=user.avatar or "",
                    bio=user.bio or "",
                )
        nodes[row.id] = MessageResponse(
            id=row.id,
            github_user_id=row.github_user_id,
            parent_id=row.parent_id,
            content=row.content,
            ip=row.ip or "",
            status=row.status,
            likes=row.likes,
            created_at=row.created_at,
            github_user=github_user,
            replies=[],
        )

    # 5.按 parent_id 挂 replies；顶层保持分页顺序
    root_ids = {row.id for row in root_rows}
    for row in all_rows:
        if row.id in root_ids:
            continue
        parent = nodes.get(row.parent_id) if row.parent_id is not None else None
        if parent is not None:
            parent.replies.append(nodes[row.id])

    # 6.回复升序
    for node in nodes.values():
        node.replies.sort(key=lambda item: item.created_at)
    roots = [nodes[row.id] for row in root_rows]

    # 7.统一结果集返回
    return Result.success(roots)


def count_messages(session: Session) -> Result:
    """统计已审核顶层留言数量。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 含 count。
    """
    # 1.统计 parent_id 为空且 approved
    count = session.exec(
        select(func.count(Message.id)).where(
            Message.parent_id.is_(None), Message.status == "approved"
        )
    ).one()

    # 2.统一结果集返回
    return Result.success(MessageCountResponse(count=count or 0))


def create_message(
    session: Session,
    CreateMessageReq: CreateMessageRequest,
    github_user: GitHubUser | None,
    ip: str,
) -> Result:
    """发表留言或回复。

    须已登录 GitHub。默认 status=approved。

    Args:
        session: 数据库会话，由路由传入。
        CreateMessageReq: 含 content、parent_id。
        github_user: 当前访客；未登录为 None。
        ip: 客户端 IP，由路由解析。

    Returns:
        统一结果集。成功时 code=200，data 为新建留言（replies 为空）。
    """
    # 1.必须 GitHub 登录
    if not github_user:
        raise HTTPException(status_code=401, detail="请先登录 GitHub")

    # 2.若是回复，父留言须存在
    if CreateMessageReq.parent_id is not None:
        parent = session.get(Message, CreateMessageReq.parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="被回复的留言不存在")

    # 3.落库（默认 approved）
    message = Message(
        github_user_id=github_user.id,
        parent_id=CreateMessageReq.parent_id,
        content=CreateMessageReq.content,
        ip=ip or "",
        status="approved",
    )
    session.add(message)
    session.commit()
    session.refresh(message)

    # 4.统一结果集返回
    return Result.success(
        MessageResponse(
            id=message.id,
            github_user_id=message.github_user_id,
            parent_id=message.parent_id,
            content=message.content,
            ip=message.ip or "",
            status=message.status,
            likes=message.likes,
            created_at=message.created_at,
            github_user=GitHubUserResponse(
                id=github_user.id,
                login=github_user.login,
                avatar=github_user.avatar or "",
                bio=github_user.bio or "",
            ),
            replies=[],
        )
    )


def toggle_message_like(
    session: Session, msg_id: int, unlike: bool = False
) -> Result:
    """给留言点赞或取消点赞。

    Args:
        session: 数据库会话，由路由传入。
        msg_id: 留言 ID。
        unlike: True 时 likes -1（最小为 0），False 时 likes +1。

    Returns:
        统一结果集。成功时 code=200，data 为留言（含最新 likes）。
    """
    # 1.留言必须存在
    message = session.get(Message, msg_id)
    if not message:
        raise HTTPException(status_code=404, detail="留言不存在")

    # 2.点赞或取消点赞并落库
    if unlike:
        message.likes = max(0, message.likes - 1)
    else:
        message.likes += 1
    session.add(message)
    session.commit()
    session.refresh(message)

    # 3.拼留言者
    github_user = None
    if message.github_user_id is not None:
        user = session.get(GitHubUser, message.github_user_id)
        if user:
            github_user = GitHubUserResponse(
                id=user.id,
                login=user.login,
                avatar=user.avatar or "",
                bio=user.bio or "",
            )

    # 4.统一结果集返回
    return Result.success(
        MessageResponse(
            id=message.id,
            github_user_id=message.github_user_id,
            parent_id=message.parent_id,
            content=message.content,
            ip=message.ip or "",
            status=message.status,
            likes=message.likes,
            created_at=message.created_at,
            github_user=github_user,
            replies=[],
        )
    )


def list_messages_admin(
    session: Session,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
) -> Result:
    """管理端：顶层留言分页，带 IP 与嵌套 replies。

    只分页顶层（parent_id 为空）；可选按 status 筛顶层。
    子回复拉全状态，按 created_at 升序挂到 replies。

    Args:
        session: 数据库会话，由路由传入。
        status: 顶层状态筛选，可选 pending / approved / rejected。
        page: 页码，从 1 开始。
        size: 每页顶层条数。

    Returns:
        统一结果集。成功时 code=200，data 为顶层留言列表（含 ip、replies）。
    """
    # 1.查顶层留言并分页（新的在前）
    query = select(Message).where(Message.parent_id.is_(None))
    if status:
        query = query.where(Message.status == status)
    query = (
        query.order_by(Message.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    root_rows = list(session.exec(query).all())

    # 2.BFS 拉齐本页顶层下的全部子孙（不限 status）
    all_rows = list(root_rows)
    frontier = [row.id for row in root_rows]
    while frontier:
        children = list(
            session.exec(
                select(Message).where(Message.parent_id.in_(frontier))
            ).all()
        )
        all_rows.extend(children)
        frontier = [child.id for child in children]

    # 3.批量取留言者
    user_ids = {
        row.github_user_id for row in all_rows if row.github_user_id is not None
    }
    users_by_id: dict[int, GitHubUser] = {}
    if user_ids:
        for user in session.exec(
            select(GitHubUser).where(GitHubUser.id.in_(user_ids))
        ).all():
            users_by_id[user.id] = user

    # 4.建成 id → MessageResponse（含 ip）
    nodes: dict[int, MessageResponse] = {}
    for row in all_rows:
        github_user = None
        if row.github_user_id is not None:
            user = users_by_id.get(row.github_user_id)
            if user:
                github_user = GitHubUserResponse(
                    id=user.id,
                    login=user.login,
                    avatar=user.avatar or "",
                    bio=user.bio or "",
                )
        nodes[row.id] = MessageResponse(
            id=row.id,
            github_user_id=row.github_user_id,
            parent_id=row.parent_id,
            content=row.content,
            ip=row.ip or "",
            status=row.status,
            likes=row.likes,
            created_at=row.created_at,
            github_user=github_user,
            replies=[],
        )

    # 5.按 parent_id 挂 replies；顶层保持分页查询顺序
    root_ids = {row.id for row in root_rows}
    for row in all_rows:
        if row.id in root_ids:
            continue
        parent = nodes.get(row.parent_id) if row.parent_id is not None else None
        if parent is not None:
            parent.replies.append(nodes[row.id])

    # 6.回复升序；顶层按查询顺序（已是 created_at 降序）
    for node in nodes.values():
        node.replies.sort(key=lambda item: item.created_at)
    roots = [nodes[row.id] for row in root_rows]

    # 7.统一结果集返回
    return Result.success(roots)


def count_messages_admin(session: Session, status: str | None = None) -> Result:
    """管理端：统计顶层留言数量。

    Args:
        session: 数据库会话，由路由传入。
        status: 可选 pending / approved / rejected；不传则全部顶层。

    Returns:
        统一结果集。成功时 code=200，data 含 count。
    """
    # 1.统计 parent_id 为空的顶层，可选 status
    query = select(func.count(Message.id)).where(Message.parent_id.is_(None))
    if status:
        query = query.where(Message.status == status)
    count = session.exec(query).one()

    # 2.统一结果集返回
    return Result.success(MessageCountResponse(count=count or 0))


def update_message_status(
    session: Session,
    msg_id: int,
    UpdateMessageStatusReq: UpdateMessageStatusRequest,
) -> Result:
    """修改留言审核状态。

    Args:
        session: 数据库会话，由路由传入。
        msg_id: 留言 ID。
        UpdateMessageStatusReq: 含 status，取值 pending / approved / rejected。

    Returns:
        统一结果集。成功时 code=200，data 为留言（含 ip，replies 为空）。
    """
    # 1.校验 status
    if UpdateMessageStatusReq.status not in _ALLOWED_MESSAGE_STATUS:
        raise HTTPException(status_code=400, detail="状态不合法")

    # 2.留言必须存在
    message = session.get(Message, msg_id)
    if not message:
        raise HTTPException(status_code=404, detail="留言不存在")

    # 3.更新并落库
    message.status = UpdateMessageStatusReq.status
    session.add(message)
    session.commit()
    session.refresh(message)

    # 4.拼留言者
    github_user = None
    if message.github_user_id is not None:
        user = session.get(GitHubUser, message.github_user_id)
        if user:
            github_user = GitHubUserResponse(
                id=user.id,
                login=user.login,
                avatar=user.avatar or "",
                bio=user.bio or "",
            )

    # 5.统一结果集返回
    return Result.success(
        MessageResponse(
            id=message.id,
            github_user_id=message.github_user_id,
            parent_id=message.parent_id,
            content=message.content,
            ip=message.ip or "",
            status=message.status,
            likes=message.likes,
            created_at=message.created_at,
            github_user=github_user,
            replies=[],
        )
    )


def delete_message(session: Session, msg_id: int) -> Result:
    """删除留言。

    先删全部子孙再删自身，避免 SQLModel create_all 未带 ON DELETE CASCADE 时留下孤儿回复。

    Args:
        session: 数据库会话，由路由传入。
        msg_id: 留言 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.留言必须存在
    message = session.get(Message, msg_id)
    if not message:
        raise HTTPException(status_code=404, detail="留言不存在")

    # 2.BFS 收集全部子孙，自深向浅删除
    to_delete = [message]
    frontier = [msg_id]
    while frontier:
        children = list(
            session.exec(
                select(Message).where(Message.parent_id.in_(frontier))
            ).all()
        )
        to_delete.extend(children)
        frontier = [child.id for child in children]
    for row in reversed(to_delete):
        session.delete(row)
    session.commit()

    # 3.统一结果集返回
    return Result.success(message="删除成功")
