from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, func, select

from app.common.Result import Result
from app.models.Category import Category
from app.models.Post import Post
from app.models.PostTag import PostTag
from app.models.Tag import Tag
from app.schemas.PostSchemas import (
    CreatePostRequest,
    PostCountResponse,
    PostDetailResponse,
    PostLikeResponse,
    PostResponse,
    UpdatePostRequest,
)


def list_posts(
    session: Session,
    status: str | None,
    category: str | None,
    tag: str | None,
    page: int,
    size: int,
) -> Result:
    """按筛选条件分页返回文章列表。

    Args:
        session: 数据库会话，由路由传入。
        status: 文章状态，可选。
        category: 分类 slug，可选。
        tag: 标签 slug，可选。
        page: 页码，从 1 开始。
        size: 每页条数。

    Returns:
        统一结果集。成功时 code=200，data 为文章列表（不含正文）。
    """
    # TODO : 后续这里需要修改代码
    # 1.组装筛选条件
    query = select(Post)
    # 状态筛选
    if status:
        query = query.where(Post.status == status)
    # 分类筛选
    if category:
        query = query.where(
            Post.category_id.in_(select(Category.id).where(Category.slug == category)))
    # 标签筛选
    if tag:
        query = query.where(
            Post.id.in_(select(PostTag.post_id).where(PostTag.tag_id.in_(select(Tag.id).where(Tag.slug == tag)))))

    # 2.置顶优先，再按创建时间倒序分页
    rows = list(session.exec( query.order_by(Post.is_pinned.desc(), Post.created_at.desc()).offset((page - 1) * size).limit(size)).all())

    # 3.批量取本页分类名、标签名
    cat_ids = {row.category_id for row in rows if row.category_id}
    cats = {
        cat.id: cat.name
        for cat in (
            session.exec(select(Category).where(Category.id.in_(cat_ids))).all()
            if cat_ids
            else []
        )
    }
    post_ids = [row.id for row in rows]
    tags_by_post: dict[int, list[str]] = {pid: [] for pid in post_ids}
    if post_ids:
        links = list(
            session.exec(select(PostTag).where(PostTag.post_id.in_(post_ids))).all()
        )
        tag_ids = {link.tag_id for link in links}
        names = {
            tag.id: tag.name
            for tag in (
                session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()
                if tag_ids
                else []
            )
        }
        for link in links:
            name = names.get(link.tag_id)
            if name:
                tags_by_post[link.post_id].append(name)

    # 4.统一结果集返回
    return Result.success(
        [
            PostResponse.model_validate(
                {
                    **row.model_dump(exclude={"content", "category_id"}),
                    "category": cats.get(row.category_id, ""),
                    "tags": tags_by_post.get(row.id, []),
                }
            )
            for row in rows
        ]
    )


def count_posts(session: Session, status: str | None) -> Result:
    """按状态统计文章数量。

    Args:
        session: 数据库会话，由路由传入。
        status: 文章状态，可选。不传则统计全部。

    Returns:
        统一结果集。成功时 code=200，data 含 count。
    """
    # 1.按状态统计
    query = select(func.count(Post.id))
    if status:
        query = query.where(Post.status == status)
    count = session.exec(query).one()

    # 2.统一结果集返回
    return Result.success(PostCountResponse(count=count or 0))


def get_post_by_id(session: Session, post_id: int) -> Result:
    """按主键取文章详情。不增加浏览量。

    Args:
        session: 数据库会话，由路由传入。
        post_id: 文章 ID。

    Returns:
        统一结果集。成功时 code=200，data 为文章详情（含正文）。
    """
    # 1.按主键取文章
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 2.取分类名
    category_name = ""
    if post.category_id:
        cat = session.get(Category, post.category_id)
        if cat:
            category_name = cat.name

    # 3.取标签名
    tag_ids = [
        link.tag_id
        for link in session.exec(select(PostTag).where(PostTag.post_id == post.id)).all()
    ]
    tag_names = []
    if tag_ids:
        tag_names = [
            tag.name
            for tag in session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()
        ]

    # 4.统一结果集返回
    return Result.success(
        PostDetailResponse.model_validate(
            {
                **post.model_dump(exclude={"category_id"}),
                "category": category_name,
                "tags": tag_names,
            }
        )
    )


def get_post_by_slug(session: Session, slug: str) -> Result:
    """按 slug 取文章详情，并增加浏览量。

    Args:
        session: 数据库会话，由路由传入。
        slug: 文章 URL 别名。

    Returns:
        统一结果集。成功时 code=200，data 为文章详情（含正文）。
    """
    # 1.按 slug 取文章
    post = session.exec(select(Post).where(Post.slug == slug)).first()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 2.浏览量 +1 并落库
    post.views += 1
    session.add(post)
    session.commit()
    session.refresh(post)

    # 3.取分类名
    category_name = ""
    if post.category_id:
        cat = session.get(Category, post.category_id)
        if cat:
            category_name = cat.name

    # 4.取标签名
    tag_ids = [
        link.tag_id
        for link in session.exec(select(PostTag).where(PostTag.post_id == post.id)).all()
    ]
    tag_names = []
    if tag_ids:
        tag_names = [
            tag.name
            for tag in session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()
        ]

    # 5.统一结果集返回
    return Result.success(
        PostDetailResponse.model_validate(
            {
                **post.model_dump(exclude={"category_id"}),
                "category": category_name,
                "tags": tag_names,
            }
        )
    )


def _update_tag_counts(session: Session) -> None:
    """按中间表重算每个标签的文章数。

    post_count 是冗余字段。改 PostTag 之后必须整表重算，
    列表里的数字才和真实关联一致（更新时旧标签也会降下来）。
    """
    for tag in session.exec(select(Tag)).all():
        tag.post_count = (
            session.exec(
                select(func.count(PostTag.post_id)).where(PostTag.tag_id == tag.id)
            ).one()
            or 0
        )
        session.add(tag)


def _update_category_count(session: Session, category_id: int | None) -> None:
    """重算某个分类下的文章数。未挂分类则跳过。"""
    if category_id is None:
        return
    cat = session.get(Category, category_id)
    if not cat:
        return
    cat.post_count = (
        session.exec(
            select(func.count(Post.id)).where(Post.category_id == category_id)
        ).one()
        or 0
    )
    session.add(cat)


def _sync_tags(session: Session, post_id: int, tag_names: list[str]) -> None:
    """按名称全量覆盖一篇文章的标签。

    先删该文全部 PostTag，再按名字找/建 Tag、写新关联，最后重算全部标签计数。
    传入 [] 表示清空标签。创建时旧关联本来就是空的。
    """
    # 1.删掉该文全部旧关联，后面按本次名单重建
    for link in session.exec(select(PostTag).where(PostTag.post_id == post_id)).all():
        session.delete(link)

    # 2.按名称逐个处理：strip、空串跳过、同一请求内同名只挂一次（避免撞联合主键）
    seen: set[str] = set()
    for raw in tag_names:
        name = raw.strip()
        if not name or name in seen:
            continue
        seen.add(name)

        # 按 name 查找；没有则创建，slug = name.lower().replace(" ", "-")
        tag = session.exec(select(Tag).where(Tag.name == name)).first()
        if not tag:
            slug = name.lower().replace(" ", "-")
            # 名称没有，但别名可能已被占用（Hello / hello 会生成同一个 slug）
            slug_taken = session.exec(select(Tag).where(Tag.slug == slug)).first()
            if slug_taken:
                raise HTTPException(status_code=400, detail="标签已存在")
            tag = Tag(name=name, slug=slug)
            session.add(tag)
            session.flush()

        session.add(PostTag(post_id=post_id, tag_id=tag.id))

    # 3.关联变了，整表重算 post_count（含本次没挂上的旧标签，计数会降下来）
    _update_tag_counts(session)


def create_post(session: Session, CreatePostReq: CreatePostRequest) -> Result:
    """创建文章。

    slug 全站唯一。tags 是标签名称不是 id。
    表上没有 tags 列，须 exclude 后再实例化 Post。

    Args:
        session: 数据库会话，由路由传入。
        CreatePostReq: 创建文章请求体。

    Returns:
        统一结果集。成功时 code=200，data 为文章（不含正文）。
    """
    # 1.slug 全站唯一：先查再插，避免撞 unique 约束变成 500
    existed = session.exec(select(Post).where(Post.slug == CreatePostReq.slug)).first()
    if existed:
        raise HTTPException(status_code=400, detail="slug 已存在")

    # 2.分类可选；传了就必须存在，否则外键失败也是 500
    if CreatePostReq.category_id is not None:
        cat = session.get(Category, CreatePostReq.category_id)
        if not cat:
            raise HTTPException(status_code=400, detail="分类不存在")

    # 3.tags 不在 post 表上，排除后再实例化
    tag_names = CreatePostReq.tags
    post = Post(**CreatePostReq.model_dump(exclude={"tags"}))

    # 4.有正文且调用方没填时，才按正文自动算字数和阅读时间
    #    阅读时间按约 300 字/分钟，至少 1 分钟
    if post.content:
        if not post.word_count:
            post.word_count = len(post.content)
        if not post.reading_time:
            post.reading_time = max(1, post.word_count // 300)

    # 5.首次变成已发布才写 published_at；草稿保持 None
    if post.status == "published" and not post.published_at:
        post.published_at = datetime.now()

    # 6.先 flush 拿到主键，后面写 PostTag 需要 post.id
    session.add(post)
    session.flush()

    # 7.有标签才同步；空列表表示本文不挂标签
    if tag_names:
        _sync_tags(session, post.id, tag_names)

    # 8.挂了分类则重算该分类的文章数
    if post.category_id:
        _update_category_count(session, post.category_id)

    session.commit()
    session.refresh(post)

    # 9.统一结果集返回：category / tags 用名称，列表 DTO 不含正文
    category_name = ""
    if post.category_id:
        cat = session.get(Category, post.category_id)
        if cat:
            category_name = cat.name
    tag_ids = [
        link.tag_id
        for link in session.exec(select(PostTag).where(PostTag.post_id == post.id)).all()
    ]
    out_tags: list[str] = []
    if tag_ids:
        out_tags = [
            tag.name
            for tag in session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()
        ]
    return Result.success(
        PostResponse.model_validate(
            {
                **post.model_dump(exclude={"content", "category_id"}),
                "category": category_name,
                "tags": out_tags,
            }
        )
    )


def update_post(
    session: Session, post_id: int, UpdatePostReq: UpdatePostRequest
) -> Result:
    """更新文章。

    只改请求里出现的字段。tags 为 None 表示不改标签，[] 表示清空。
    换分类时旧分类和新分类的文章数都要重算。

    Args:
        session: 数据库会话，由路由传入。
        post_id: 文章 ID。
        UpdatePostReq: 更新文章请求体。

    Returns:
        统一结果集。成功时 code=200，data 为文章（不含正文）。
    """
    # 1.文章必须存在
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 2.slug 若要改，须全站唯一（排除自身）
    if UpdatePostReq.slug is not None:
        existed = session.exec(
            select(Post).where(
                (Post.slug == UpdatePostReq.slug) & (Post.id != post_id)
            )
        ).first()
        if existed:
            raise HTTPException(status_code=400, detail="slug 已存在")

    # 3.分类若要改成某个 id，该分类必须存在；传 null 表示去掉分类
    if UpdatePostReq.category_id is not None:
        cat = session.get(Category, UpdatePostReq.category_id)
        if not cat:
            raise HTTPException(status_code=400, detail="分类不存在")

    # 4.只落调用方真正传入的字段；tags 不在 post 表上，单独处理
    tag_names = UpdatePostReq.tags
    update_data = UpdatePostReq.model_dump(exclude_unset=True, exclude={"tags"})
    old_category = post.category_id
    for key, value in update_data.items():
        setattr(post, key, value)

    # 5.有正文且本次没手动传字数/阅读时间时，按正文重算
    #    阅读时间按约 300 字/分钟，至少 1 分钟
    if post.content:
        if "word_count" not in update_data:
            post.word_count = len(post.content)
        if "reading_time" not in update_data:
            post.reading_time = max(1, post.word_count // 300)

    # 6.首次变成已发布才写 published_at；已有值不覆盖
    if post.status == "published" and not post.published_at:
        post.published_at = datetime.now()

    # 7.刷新更新时间并 flush，后续改关联需要当前字段已生效
    post.updated_at = datetime.now()
    session.add(post)
    session.flush()

    # 8.tags is not None 才同步；传 [] 会删光旧关联
    if tag_names is not None:
        _sync_tags(session, post.id, tag_names)

    # 9.换分类时旧、新两边都要重算；没换则只算一次
    _update_category_count(session, old_category)
    if post.category_id != old_category:
        _update_category_count(session, post.category_id)

    session.commit()
    session.refresh(post)

    # 10.统一结果集返回：category / tags 用名称，列表 DTO 不含正文
    category_name = ""
    if post.category_id:
        cat = session.get(Category, post.category_id)
        if cat:
            category_name = cat.name
    tag_ids = [
        link.tag_id
        for link in session.exec(select(PostTag).where(PostTag.post_id == post.id)).all()
    ]
    out_tags: list[str] = []
    if tag_ids:
        out_tags = [
            tag.name
            for tag in session.exec(select(Tag).where(Tag.id.in_(tag_ids))).all()
        ]
    return Result.success(
        PostResponse.model_validate(
            {
                **post.model_dump(exclude={"content", "category_id"}),
                "category": category_name,
                "tags": out_tags,
            }
        )
    )


def like_post(session: Session, post_id: int, unliked: bool = False) -> Result:
    """给文章点赞或取消点赞。

    Args:
        session: 数据库会话，由路由传入。
        post_id: 文章 ID。
        unliked: True 时 likes -1（最小为 0），False 时 likes +1。

    Returns:
        统一结果集。成功时 code=200，data 含 likes。
    """
    # 1.文章必须存在
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 2.点赞或取消点赞并落库
    if unliked:
        post.likes = max(0, post.likes - 1)
    else:
        post.likes += 1
    session.add(post)
    session.commit()
    session.refresh(post)

    # 3.统一结果集返回
    return Result.success(PostLikeResponse(likes=post.likes))


def delete_post(session: Session, post_id: int) -> Result:
    """删除文章。

    删掉后重算所属分类和全部标签的文章数。
    post_tag 有 ON DELETE CASCADE，删文章会带走关联行。

    Args:
        session: 数据库会话，由路由传入。
        post_id: 文章 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.文章必须存在
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 2.记下分类，删完后要重算该分类文章数
    category_id = post.category_id

    # 3.删除文章并 flush，级联清掉 post_tag
    session.delete(post)
    session.flush()

    # 4.重算所属分类和全部标签的文章数
    _update_category_count(session, category_id)
    _update_tag_counts(session)

    # 5.落库
    session.commit()

    # 6.统一结果集返回
    return Result.success(message="删除成功")
