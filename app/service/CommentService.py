from fastapi import HTTPException
from sqlmodel import Session, select

from app.common.Result import Result
from app.models.Comment import Comment
from app.models.GitHubUser import GitHubUser
from app.models.Post import Post
from app.schemas.CommentSchemas import (
    CommentAdminResponse,
    CommentResponse,
    CreateCommentRequest,
    UpdateCommentStatusRequest,
)
from app.schemas.GitHubAuthSchemas import GitHubUserResponse

# 评论审核状态允许取值
_ALLOWED_COMMENT_STATUS = {"pending", "approved", "rejected"}


def get_comments_by_post(session: Session, post_id: int) -> Result:
    """按文章取已审核评论树。

    只返回 status=approved。顶层按 created_at 降序，回复按 created_at 升序挂到 replies。
    父评论不在结果集（例如被拒）时，子评论会落成顶层「假根」。

    Args:
        session: 数据库会话，由路由传入。
        post_id: 文章 ID。

    Returns:
        统一结果集。成功时 code=200，data 为顶层评论列表（含 replies）。
    """
    # 1.查该文章全部已审核评论（前台不展示 pending / rejected）
    rows = list(
        session.exec(
            select(Comment).where(
                Comment.post_id == post_id, Comment.status == "approved"
            )
        ).all()
    )

    # 2.收集评论者本地主键，一次查出，避免每条评论再查一次用户
    user_ids = {row.github_user_id for row in rows if row.github_user_id is not None}
    users_by_id: dict[int, GitHubUser] = {}
    if user_ids:
        for user in session.exec(
            select(GitHubUser).where(GitHubUser.id.in_(user_ids))
        ).all():
            users_by_id[user.id] = user

    # 3.先建成 id → CommentResponse；replies 先空着，下一步再挂
    nodes: dict[int, CommentResponse] = {}
    for row in rows:
        # 3.1 拼嵌套的 github_user；用户已删或外键为空则为 null
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
        # 3.2 扁平节点入 map，用评论主键当 key
        nodes[row.id] = CommentResponse(
            id=row.id,
            post_id=row.post_id,
            parent_id=row.parent_id,
            content=row.content,
            likes=row.likes,
            status=row.status,
            created_at=row.created_at,
            github_user=github_user,
            replies=[],
        )

    # 4.第二次遍历：按 parent_id 挂树
    roots: list[CommentResponse] = []
    for row in rows:
        node = nodes[row.id]
        # 4.1 父评论在本次结果里 → 挂到父的 replies（楼中楼）
        if row.parent_id is not None and row.parent_id in nodes:
            nodes[row.parent_id].replies.append(node)
        # 4.2 顶层，或父不在集里（如父被拒审）→ 进 roots，后者即「假根」
        else:
            roots.append(node)

    # 5.排序：顶层新的在前；同一父下的回复旧的在前
    roots.sort(key=lambda item: item.created_at, reverse=True)
    for node in nodes.values():
        node.replies.sort(key=lambda item: item.created_at)

    # 6.统一结果集返回（只返回顶层，子回复已在 replies 里）
    return Result.success(roots)


def create_comment(
    session: Session,
    CreateCommentReq: CreateCommentRequest,
    github_user: GitHubUser | None,
    ip: str,
) -> Result:
    """发表评论或回复。

    须已登录 GitHub。默认 status=approved，发表后前台立刻可见。

    Args:
        session: 数据库会话，由路由传入。
        CreateCommentReq: 发表请求体，含 post_id、parent_id、content。
        github_user: 当前访客；未登录为 None。
        ip: 客户端 IP，由路由从 Header / client 解析。

    Returns:
        统一结果集。成功时 code=200，data 为新建评论（replies 为空数组）。
    """
    # 1.必须 GitHub 登录
    if not github_user:
        raise HTTPException(status_code=401, detail="请先登录 GitHub")

    # 2.文章须存在
    post = session.get(Post, CreateCommentReq.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 3.若是回复，父评论须存在且属于同一文章
    if CreateCommentReq.parent_id is not None:
        parent = session.get(Comment, CreateCommentReq.parent_id)
        if not parent or parent.post_id != CreateCommentReq.post_id:
            raise HTTPException(status_code=404, detail="被回复的评论不存在")

    # 4.落库（默认 approved）
    comment = Comment(
        post_id=CreateCommentReq.post_id,
        parent_id=CreateCommentReq.parent_id,
        github_user_id=github_user.id,
        content=CreateCommentReq.content,
        ip=ip or "",
        status="approved",
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)

    # 5.统一结果集返回（新建尚无子回复）
    return Result.success(
        CommentResponse(
            id=comment.id,
            post_id=comment.post_id,
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


def toggle_comment_like(
    session: Session, comment_id: int, unlike: bool = False
) -> Result:
    """给评论点赞或取消点赞。

    Args:
        session: 数据库会话，由路由传入。
        comment_id: 评论 ID。
        unlike: True 时 likes -1（最小为 0），False 时 likes +1。

    Returns:
        统一结果集。成功时 code=200，data 为评论（含最新 likes，replies 为空）。
    """
    # 1.评论必须存在
    comment = session.get(Comment, comment_id)
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
        CommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            parent_id=comment.parent_id,
            content=comment.content,
            likes=comment.likes,
            status=comment.status,
            created_at=comment.created_at,
            github_user=github_user,
            replies=[],
        )
    )


def list_comments_admin(
    session: Session,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
) -> Result:
    """管理端：顶层评论分页，带 IP 与嵌套 replies。

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
    query = select(Comment).where(Comment.parent_id.is_(None))
    if status:
        query = query.where(Comment.status == status)
    query = (
        query.order_by(Comment.created_at.desc())
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
                select(Comment).where(Comment.parent_id.in_(frontier))
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

    # 4.建成 id → CommentAdminResponse（含 ip）
    nodes: dict[int, CommentAdminResponse] = {}
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
        nodes[row.id] = CommentAdminResponse(
            id=row.id,
            post_id=row.post_id,
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


def update_comment_status(
    session: Session,
    comment_id: int,
    UpdateCommentStatusReq: UpdateCommentStatusRequest,
) -> Result:
    """修改评论审核状态。

    Args:
        session: 数据库会话，由路由传入。
        comment_id: 评论 ID。
        UpdateCommentStatusReq: 含 status，取值 pending / approved / rejected。

    Returns:
        统一结果集。成功时 code=200，data 为评论（含 ip，replies 为空）。
    """
    # 1.校验 status
    if UpdateCommentStatusReq.status not in _ALLOWED_COMMENT_STATUS:
        raise HTTPException(status_code=400, detail="状态不合法")

    # 2.评论必须存在
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 3.更新并落库
    comment.status = UpdateCommentStatusReq.status
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
        CommentAdminResponse(
            id=comment.id,
            post_id=comment.post_id,
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


def delete_comment(session: Session, comment_id: int) -> Result:
    """删除评论。

    先删全部子孙再删自身，避免 SQLModel create_all 未带 ON DELETE CASCADE 时留下孤儿回复。

    Args:
        session: 数据库会话，由路由传入。
        comment_id: 评论 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.评论必须存在
    comment = session.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    # 2.BFS 收集全部子孙，自深向浅删除
    to_delete = [comment]
    frontier = [comment_id]
    while frontier:
        children = list(
            session.exec(
                select(Comment).where(Comment.parent_id.in_(frontier))
            ).all()
        )
        to_delete.extend(children)
        frontier = [child.id for child in children]
    for row in reversed(to_delete):
        session.delete(row)
    session.commit()

    # 3.统一结果集返回
    return Result.success(message="删除成功")
