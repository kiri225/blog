from fastapi import HTTPException
from sqlmodel import Session, select

from app.common.Result import Result
from app.models.Tag import Tag
from app.schemas.TagSchemas import CreateTagRequest, UpdateTagRequest


def get_tags(session: Session) -> Result:
    """按 id 正序返回全部标签。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为标签列表。
    """
    # 1.按 id 正序查询
    tags_data = list(session.exec(select(Tag).order_by(Tag.id)).all())

    # 2.统一结果集返回
    return Result.success(tags_data)


def create_tag(session: Session, CreateTagReq: CreateTagRequest) -> Result:
    """创建标签。

    Args:
        session: 数据库会话，由路由传入。
        CreateTagReq: 创建标签请求体。

    Returns:
        统一结果集。成功时 code=200，data 为标签。
    """
    # 1.判断名称或别名是否已存在
    existed = session.exec(
        select(Tag).where(
            (Tag.name == CreateTagReq.name) | (Tag.slug == CreateTagReq.slug)
        )
    ).first()
    if existed:
        raise HTTPException(status_code=400, detail="标签已存在")

    # 2.落库
    tag = Tag(name=CreateTagReq.name, slug=CreateTagReq.slug)
    session.add(tag)
    session.commit()
    session.refresh(tag)

    # 3.统一结果集返回
    return Result.success(tag)


def update_tag(
    session: Session, tag_id: int, UpdateTagReq: UpdateTagRequest
) -> Result:
    """更新标签。

    Args:
        session: 数据库会话，由路由传入。
        tag_id: 标签 ID。
        UpdateTagReq: 更新标签请求体。

    Returns:
        统一结果集。成功时 code=200，data 为标签。
    """
    # 1.判断标签是否存在
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 2.判断名称或别名是否被其它标签占用
    # 获取更新后的名称或别名
    name = UpdateTagReq.name if UpdateTagReq.name is not None else tag.name
    # 获取更新后的别名
    slug = UpdateTagReq.slug if UpdateTagReq.slug is not None else tag.slug
    # 判断名称或别名是否被其它标签占用
    existed = session.exec(
        select(Tag).where(
            ((Tag.name == name) | (Tag.slug == slug)) & (Tag.id != tag_id)
        )
    ).first()
    # 如果被占用，抛出400错误码 并提示被占用
    if existed:
        raise HTTPException(status_code=400, detail="标签被占用")

    # 3.按传入字段更新
    if UpdateTagReq.name is not None:
        tag.name = UpdateTagReq.name
    if UpdateTagReq.slug is not None:
        tag.slug = UpdateTagReq.slug

    # 4.落库
    session.commit()
    session.refresh(tag)

    # 5.统一结果集返回
    return Result.success(tag)


def delete_tag(session: Session, tag_id: int) -> Result:
    """删除标签。

    Args:
        session: 数据库会话，由路由传入。
        tag_id: 标签 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.判断标签是否存在
    tag = session.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")

    # 2.判断是否仍有文章占用
    if tag.post_count > 0:
        raise HTTPException(status_code=400, detail="标签被文章引用，不能删除")

    # 3.删除并落库
    session.delete(tag)
    session.commit()

    # 4.统一结果集返回
    return Result.success(message="删除成功")


