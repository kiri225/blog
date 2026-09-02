import json
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.common.Result import Result
from app.models.Chatter import Chatter
from app.models.ChatterComment import ChatterComment
from app.models.GitHubUser import GitHubUser
from app.schemas.ChatterSchemas import (
    ChatterCommentAdminResponse,
    ChatterCommentResponse,
    ChatterCountResponse,
    ChatterLikeResponse,
    CreateChatterCommentRequest,
    CreateChatterRequest,
    UpdateChatterCommentStatusRequest,
    UpdateChatterRequest,
)
from app.schemas.GitHubAuthSchemas import GitHubUserResponse

_ALLOWED_CHATTER_STATUS = {"draft", "published"}
_ALLOWED_COMMENT_STATUS = {"pending", "approved", "rejected"}


def get_chatters(
    session: Session, status: str | None, page: int, size: int
) -> Result:
    """按状态分页返回说说列表。

    Args:
        session: 数据库会话，由路由传入。
        status: 说说状态，如 published；None 或空串表示全部。
        page: 页码，从 1 开始。
        size: 每页条数。

    Returns:
        统一结果集。成功时 code=200，data 为说说列表。
    """
    # 1.按状态筛选，创建时间降序分页
    query = select(Chatter)
    if status:
        query = query.where(Chatter.status == status)
    chatters_info = list(
        session.exec(
            query.order_by(Chatter.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        ).all()
    )

    # 2.统一结果集返回
    return Result.success(chatters_info)


def get_chatter_count(session: Session, status: str) -> Result:
    """按状态统计说说数量。

    Args:
        session: 数据库会话，由路由传入。
        status: 说说状态，如 published。空串则统计全部。

    Returns:
        统一结果集。成功时 code=200，data 含 count。
    """
    # 1.按状态统计
    chatter_count = select(func.count(Chatter.id))
    if status:
        chatter_count = chatter_count.where(Chatter.status == status)
    count = session.exec(chatter_count).one()

    # 2.统一结果集返回
    return Result.success(ChatterCountResponse(count=count or 0))


def get_chatter_by_id(session: Session, chatter_id: int) -> Result:
    """按主键取说说详情。

    Args:
        session: 数据库会话，由路由传入。
        chatter_id: 说说 ID。

    Returns:
        统一结果集。成功时 code=200，data 为说说。
    """
    # 1.按主键取说说
    chatter = session.get(Chatter, chatter_id)
    if not chatter:
        raise HTTPException(status_code=404, detail="说说不存在")

    # 2.统一结果集返回
    return Result.success(chatter)


def create_chatter(
    session: Session, CreateChatterReq: CreateChatterRequest
) -> Result:
    """管理员创建说说。

    Args:
        session: 数据库会话，由路由传入。
        CreateChatterReq: 创建说说请求体。

    Returns:
        统一结果集。成功时 code=200，data 为说说。
    """
    # 1.校验 status
    if CreateChatterReq.status not in _ALLOWED_CHATTER_STATUS:
        raise HTTPException(status_code=400, detail="状态不合法")

    # 2.落库（images 转 JSON 字符串）
    chatter = Chatter(
        content=CreateChatterReq.content,
        images=json.dumps(CreateChatterReq.images, ensure_ascii=False),
        mood=CreateChatterReq.mood or "",
        status=CreateChatterReq.status,
    )
    session.add(chatter)
    session.commit()
    session.refresh(chatter)

    # 3.统一结果集返回
    return Result.success(chatter)


def update_chatter(
    session: Session,
    chatter_id: int,
    UpdateChatterReq: UpdateChatterRequest,
) -> Result:
    """管理员更新说说。只改传入字段。

    Args:
        session: 数据库会话，由路由传入。
        chatter_id: 说说 ID。
        UpdateChatterReq: 更新说说请求体。

    Returns:
        统一结果集。成功时 code=200，data 为说说。
    """
    # 1.说说必须存在
    chatter = session.get(Chatter, chatter_id)
    if not chatter:
        raise HTTPException(status_code=404, detail="说说不存在")

    # 2.校验 status（若传入）
    if (
        UpdateChatterReq.status is not None
        and UpdateChatterReq.status not in _ALLOWED_CHATTER_STATUS
    ):
        raise HTTPException(status_code=400, detail="状态不合法")

    # 3.按传入字段更新
    if UpdateChatterReq.content is not None:
        chatter.content = UpdateChatterReq.content
    if UpdateChatterReq.images is not None:
        chatter.images = json.dumps(UpdateChatterReq.images, ensure_ascii=False)
    if UpdateChatterReq.mood is not None:
        chatter.mood = UpdateChatterReq.mood
    if UpdateChatterReq.status is not None:
        chatter.status = UpdateChatterReq.status
    chatter.updated_at = datetime.now()

    # 4.落库
    session.add(chatter)
    session.commit()
    session.refresh(chatter)

    # 5.统一结果集返回
    return Result.success(chatter)


def delete_chatter(session: Session, chatter_id: int) -> Result:
    """管理员删除说说。

    先删该说说下全部评论（含楼中楼），再删说说本身。

    Args:
        session: 数据库会话，由路由传入。
        chatter_id: 说说 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.说说必须存在
    chatter = session.get(Chatter, chatter_id)
    if not chatter:
        raise HTTPException(status_code=404, detail="说说不存在")

    # 2.收集该说说下全部评论，自深向浅删除
    all_rows = list(
        session.exec(
            select(ChatterComment).where(ChatterComment.chatter_id == chatter_id)
        ).all()
    )
    id_set = {row.id for row in all_rows}
    children: dict[int | None, list[int]] = {}
    for row in all_rows:
        key = row.parent_id if row.parent_id in id_set else None
        children.setdefault(key, []).append(row.id)
    ordered: list[int] = []
    frontier = list(children.get(None, []))
    while frontier:
        ordered.extend(frontier)
        next_frontier: list[int] = []
        for parent_id in frontier:
            next_frontier.extend(children.get(parent_id, []))
        frontier = next_frontier
    by_id = {row.id: row for row in all_rows}
    for comment_id in reversed(ordered):
        session.delete(by_id[comment_id])

    # 3.删除说说并落库
    session.delete(chatter)
    session.commit()

    # 4.统一结果集返回
    return Result.success(message="删除成功")


def get_chatter_comments(session: Session, chatter_id: int) -> Result:
    """按说说取已审核评论树。

    只返回 status=approved。顶层按 created_at 降序，回复按 created_at 升序挂到 replies。
    父评论不在结果集（例如被拒）时，子评论会落成顶层「假根」。

    Args:
        session: 数据库会话，由路由传入。
        chatter_id: 说说 ID。

    Returns:
        统一结果集。成功时 code=200，data 为顶层评论列表（含 replies）。
    """
    # 1.查该说说全部已审核评论（前台不展示 pending / rejected）
    rows = list(
        session.exec(
            select(ChatterComment).where(
                ChatterComment.chatter_id == chatter_id,
                ChatterComment.status == "approved",
            )
        ).all()
    )

    # 2.收集评论者本地主键，一次查出
    user_ids = {row.github_user_id for row in rows if row.github_user_id is not None}
    users_by_id: dict[int, GitHubUser] = {}
    if user_ids:
        for user in session.exec(
            select(GitHubUser).where(GitHubUser.id.in_(user_ids))
        ).all():
            users_by_id[user.id] = user

    # 3.先建成 id → ChatterCommentResponse；replies 先空着
    nodes: dict[int, ChatterCommentResponse] = {}
    for row in rows:
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
        nodes[row.id] = ChatterCommentResponse(
            id=row.id,
            chatter_id=row.chatter_id,
            parent_id=row.parent_id,
            content=row.content,
            likes=row.likes,
            status=row.status,
            created_at=row.created_at,
            github_user=github_user,
            replies=[],
        )

    # 4.按 parent_id 挂树
    roots: list[ChatterCommentResponse] = []
    for row in rows:
        node = nodes[row.id]
        if row.parent_id is not None and row.parent_id in nodes:
            nodes[row.parent_id].replies.append(node)
        else:
            roots.append(node)

    # 5.排序：顶层新的在前；同一父下的回复旧的在前
    roots.sort(key=lambda item: item.created_at, reverse=True)
    for node in nodes.values():
        node.replies.sort(key=lambda item: item.created_at)

    # 6.统一结果集返回
    return Result.success(roots)


def create_chatter_comment(
    session: Session,
    CreateChatterCommentReq: CreateChatterCommentRequest,
    github_user: GitHubUser | None,
    ip: str,
) -> Result:
    """发表说说评论或回复。

    须已登录 GitHub。默认 status=approved，发表后前台立刻可见。

    Args:
        session: 数据库会话，由路由传入。
        CreateChatterCommentReq: 发表请求体，含 chatter_id、parent_id、content。
        github_user: 当前访客；未登录为 None。
        ip: 客户端 IP，由路由从 Header / client 解析。

    Returns:
        统一结果集。成功时 code=200，data 为新建评论（replies 为空数组）。
    """
    # 1.必须 GitHub 登录
    if not github_user:
        raise HTTPException(status_code=401, detail="请先登录 GitHub")

    # 2.说说须存在
    chatter = session.get(Chatter, CreateChatterCommentReq.chatter_id)
    if not chatter:
        raise HTTPException(status_code=404, detail="说说不存在")

    # 3.若是回复，父评论须存在且属于同一说说
    if CreateChatterCommentReq.parent_id is not None:
        parent = session.get(ChatterComment, CreateChatterCommentReq.parent_id)
        if not parent or parent.chatter_id != CreateChatterCommentReq.chatter_id:
            raise HTTPException(status_code=404, detail="被回复的评论不存在")

    # 4.落库（默认 approved），说说评论数 +1
    comment = ChatterComment(
        chatter_id=CreateChatterCommentReq.chatter_id,
        parent_id=CreateChatterCommentReq.parent_id,
        github_user_id=github_user.id,
        content=CreateChatterCommentReq.content,
        ip=ip or "",
        status="approved",
    )
    session.add(comment)
    chatter.comments_count += 1
    chatter.updated_at = datetime.now()
    session.commit()
    session.refresh(comment)

    # 5.统一结果集返回（新建尚无子回复）
    return Result.success(
        ChatterCommentResponse(
            id=comment.id,
            chatter_id=comment.chatter_id,
            parent_id=comment.parent_id,
            content=comment.content,
            likes=comment.likes,
            status=comment.status,
            created_at=comment.created_at,
            github_user=GitHubUserResponse(
                id=github_user.id,
                login=github_user.login,
                avatar=github_user.avatar or "",
                bio=github_user.bio or "",
            ),
            replies=[],
        )
    )


def list_chatter_comments_admin(
    session: Session,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
) -> Result:
    """管理端：顶层说说评论分页，带 IP 与嵌套 replies。

    只分页顶层（parent_id 为空）；可选按 status 筛顶层。
    子回复拉全状态，按 created_at 升序挂到 replies。

    Args:
        session: 数据库会话，由路由传入。
        status: 顶层状态筛选，可选 pending / approved / rejected。
        page: 页码，从 1 开始。
        size: 每页顶层条数。

    Returns:
        统一结果集。成功时 code=200，data 为顶层评论列表（含 ip、replies）。
    """
    # 1.查顶层评论并分页（新的在前）
    query = select(ChatterComment).where(ChatterComment.parent_id.is_(None))
    if status:
        query = query.where(ChatterComment.status == status)
    query = (
        query.order_by(ChatterComment.created_at.desc())
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
                select(ChatterComment).where(ChatterComment.parent_id.in_(frontier))
            ).all()
        )
        all_rows.extend(children)
        frontier = [child.id for child in children]

    # 3.批量取评论者
    user_ids = {
        row.github_user_id for row in all_rows if row.github_user_id is not None
    }
    users_by_id: dict[int, GitHubUser] = {}
    if user_ids:
        for user in session.exec(
            select(GitHubUser).where(GitHubUser.id.in_(user_ids))
        ).all():
            users_by_id[user.id] = user

    # 4.建成 id → ChatterCommentAdminResponse（含 ip）
    nodes: dict[int, ChatterCommentAdminResponse] = {}
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
        nodes[row.id] = ChatterCommentAdminResponse(
            id=row.id,
            chatter_id=row.chatter_id,
            parent_id=row.parent_id,
            content=row.content,
            likes=row.likes,
            status=row.status,
            ip=row.ip or "",
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


def update_chatter_comment_status(
    session: Session,
    comment_id: int,
    UpdateChatterCommentStatusReq: UpdateChatterCommentStatusRequest,
) -> Result:
    """修改说说评论审核状态。

    Args:
        session: 数据库会话，由路由传入。
        comment_id: 评论 ID。
        UpdateChatterCommentStatusReq: 含 status，取值 pending / approved / rejected。

    Returns:
        统一结果集。成功时 code=200，data 为评论（含 ip，replies 为空）。
    """
    # 1.校验 status
    if UpdateChatterCommentStatusReq.status not in _ALLOWED_COMMENT_STATUS:
        raise HTTPException(status_code=400, detail="状态不合法")

    # 2.评论必须存在
    comment = session.get(ChatterComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 3.更新并落库
    comment.status = UpdateChatterCommentStatusReq.status
    session.add(comment)
    session.commit()
    session.refresh(comment)

    # 4.拼评论者
    github_user = None
    if comment.github_user_id is not None:
        user = session.get(GitHubUser, comment.github_user_id)
        if user:
            github_user = GitHubUserResponse(
                id=user.id,
                login=user.login,
                avatar=user.avatar or "",
                bio=user.bio or "",
            )

    # 5.统一结果集返回
    return Result.success(
        ChatterCommentAdminResponse(
            id=comment.id,
            chatter_id=comment.chatter_id,
            parent_id=comment.parent_id,
            content=comment.content,
            likes=comment.likes,
            status=comment.status,
            ip=comment.ip or "",
            created_at=comment.created_at,
            github_user=github_user,
            replies=[],
        )
    )


def delete_chatter_comment(session: Session, comment_id: int) -> Result:
    """删除说说评论。

    先删全部子孙再删自身；说说 comments_count 按删除条数减少（最小 0）。

    Args:
        session: 数据库会话，由路由传入。
        comment_id: 评论 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.评论必须存在
    comment = session.get(ChatterComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    chatter_id = comment.chatter_id

    # 2.BFS 收集全部子孙，自深向浅删除
    to_delete = [comment]
    frontier = [comment_id]
    while frontier:
        children = list(
            session.exec(
                select(ChatterComment).where(ChatterComment.parent_id.in_(frontier))
            ).all()
        )
        to_delete.extend(children)
        frontier = [child.id for child in children]
    for row in reversed(to_delete):
        session.delete(row)

    # 3.说说评论数按删除条数回减
    chatter = session.get(Chatter, chatter_id)
    if chatter:
        chatter.comments_count = max(0, chatter.comments_count - len(to_delete))
        chatter.updated_at = datetime.now()
        session.add(chatter)

    session.commit()

    # 4.统一结果集返回
    return Result.success(message="删除成功")


def toggle_chatter_like(
    session: Session, chatter_id: int, unlike: bool = False
) -> Result:
    """给说说点赞或取消点赞。

    Args:
        session: 数据库会话，由路由传入。
        chatter_id: 说说 ID。
        unlike: True 时 likes -1（最小为 0），False 时 likes +1。

    Returns:
        统一结果集。成功时 code=200，data 含 likes。
    """
    # 1.说说必须存在
    chatter = session.get(Chatter, chatter_id)
    if not chatter:
        raise HTTPException(status_code=404, detail="说说不存在")

    # 2.点赞或取消点赞并落库
    if unlike:
        chatter.likes = max(0, chatter.likes - 1)
    else:
        chatter.likes += 1
    chatter.updated_at = datetime.now()
    session.add(chatter)
    session.commit()
    session.refresh(chatter)

    # 3.统一结果集返回
    return Result.success(ChatterLikeResponse(likes=chatter.likes))


def toggle_chatter_comment_like(
    session: Session, comment_id: int, unlike: bool = False
) -> Result:
    """给说说评论点赞或取消点赞。

    Args:
        session: 数据库会话，由路由传入。
        comment_id: 说说评论 ID。
        unlike: True 时 likes -1（最小为 0），False 时 likes +1。

    Returns:
        统一结果集。成功时 code=200，data 为评论（含最新 likes，replies 为空）。
    """
    # 1.评论必须存在
    comment = session.get(ChatterComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 2.点赞或取消点赞并落库
    if unlike:
        comment.likes = max(0, comment.likes - 1)
    else:
        comment.likes += 1
    session.add(comment)
    session.commit()
    session.refresh(comment)

    # 3.拼评论者（用户已删则为 null）
    github_user = None
    if comment.github_user_id is not None:
        user = session.get(GitHubUser, comment.github_user_id)
        if user:
            github_user = GitHubUserResponse(
                id=user.id,
                login=user.login,
                avatar=user.avatar or "",
                bio=user.bio or "",
            )

    # 4.统一结果集返回
    return Result.success(
        ChatterCommentResponse(
            id=comment.id,
            chatter_id=comment.chatter_id,
            parent_id=comment.parent_id,
            content=comment.content,
            likes=comment.likes,
            status=comment.status,
            created_at=comment.created_at,
            github_user=github_user,
            replies=[],
        )
    )
