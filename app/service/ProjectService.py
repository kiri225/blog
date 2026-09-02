import json
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.common.Result import Result
from app.models.Project import Project
from app.schemas.ProjectSchemas import CreateProjectRequest, UpdateProjectRequest

_ALLOWED_PROJECT_STATUS = {"developing", "active", "archived"}


def list_projects(session: Session) -> Result:
    """按 sort 升序返回全部项目。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为项目列表。
    """
    # 1.按 sort 升序查询
    rows = list(session.exec(select(Project).order_by(Project.sort)).all())

    # 2.统一结果集返回
    return Result.success(rows)


def get_project_by_slug(session: Session, slug: str) -> Result:
    """按 slug 取项目详情。

    Args:
        session: 数据库会话，由路由传入。
        slug: 项目 URL 别名。

    Returns:
        统一结果集。成功时 code=200，data 为项目。
    """
    # 1.按 slug 取项目
    project = session.exec(select(Project).where(Project.slug == slug)).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2.统一结果集返回
    return Result.success(project)


def create_project(
    session: Session, CreateProjectReq: CreateProjectRequest
) -> Result:
    """管理员创建项目。

    Args:
        session: 数据库会话，由路由传入。
        CreateProjectReq: 创建项目请求体。

    Returns:
        统一结果集。成功时 code=200，data 为项目。
    """
    # 1.slug 全站唯一
    existed = session.exec(
        select(Project).where(Project.slug == CreateProjectReq.slug)
    ).first()
    if existed:
        raise HTTPException(status_code=400, detail="slug 已存在")

    # 2.校验 status
    if CreateProjectReq.status not in _ALLOWED_PROJECT_STATUS:
        raise HTTPException(status_code=400, detail="状态不合法")

    # 3.落库（tech_stack 转 JSON 字符串）
    project = Project(
        name=CreateProjectReq.name,
        slug=CreateProjectReq.slug,
        description=CreateProjectReq.description or "",
        long_description=CreateProjectReq.long_description or "",
        cover_image=CreateProjectReq.cover_image or "",
        tech_stack=json.dumps(CreateProjectReq.tech_stack, ensure_ascii=False),
        link_github=CreateProjectReq.link_github or "",
        link_gitee=CreateProjectReq.link_gitee or "",
        link_live=CreateProjectReq.link_live or "",
        link_docs=CreateProjectReq.link_docs or "",
        status=CreateProjectReq.status,
        status_label=CreateProjectReq.status_label or "",
        is_featured=CreateProjectReq.is_featured,
        sort=CreateProjectReq.sort,
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    # 4.统一结果集返回
    return Result.success(project)


def update_project(
    session: Session, project_id: int, UpdateProjectReq: UpdateProjectRequest
) -> Result:
    """管理员更新项目。只改传入字段。

    Args:
        session: 数据库会话，由路由传入。
        project_id: 项目 ID。
        UpdateProjectReq: 更新项目请求体。

    Returns:
        统一结果集。成功时 code=200，data 为项目。
    """
    # 1.项目必须存在
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2.slug 若传入则须全站唯一（排除自身）
    if UpdateProjectReq.slug is not None:
        existed = session.exec(
            select(Project).where(
                (Project.slug == UpdateProjectReq.slug) & (Project.id != project_id)
            )
        ).first()
        if existed:
            raise HTTPException(status_code=400, detail="slug 已存在")

    # 3.校验 status（若传入）
    if (
        UpdateProjectReq.status is not None
        and UpdateProjectReq.status not in _ALLOWED_PROJECT_STATUS
    ):
        raise HTTPException(status_code=400, detail="状态不合法")

    # 4.按传入字段更新
    if UpdateProjectReq.name is not None:
        project.name = UpdateProjectReq.name
    if UpdateProjectReq.slug is not None:
        project.slug = UpdateProjectReq.slug
    if UpdateProjectReq.description is not None:
        project.description = UpdateProjectReq.description
    if UpdateProjectReq.long_description is not None:
        project.long_description = UpdateProjectReq.long_description
    if UpdateProjectReq.cover_image is not None:
        project.cover_image = UpdateProjectReq.cover_image
    if UpdateProjectReq.tech_stack is not None:
        project.tech_stack = json.dumps(
            UpdateProjectReq.tech_stack, ensure_ascii=False
        )
    if UpdateProjectReq.link_github is not None:
        project.link_github = UpdateProjectReq.link_github
    if UpdateProjectReq.link_gitee is not None:
        project.link_gitee = UpdateProjectReq.link_gitee
    if UpdateProjectReq.link_live is not None:
        project.link_live = UpdateProjectReq.link_live
    if UpdateProjectReq.link_docs is not None:
        project.link_docs = UpdateProjectReq.link_docs
    if UpdateProjectReq.status is not None:
        project.status = UpdateProjectReq.status
    if UpdateProjectReq.status_label is not None:
        project.status_label = UpdateProjectReq.status_label
    if UpdateProjectReq.is_featured is not None:
        project.is_featured = UpdateProjectReq.is_featured
    if UpdateProjectReq.sort is not None:
        project.sort = UpdateProjectReq.sort
    project.updated_at = datetime.now()

    # 5.落库
    session.add(project)
    session.commit()
    session.refresh(project)

    # 6.统一结果集返回
    return Result.success(project)


def delete_project(session: Session, project_id: int) -> Result:
    """管理员删除项目。

    Args:
        session: 数据库会话，由路由传入。
        project_id: 项目 ID。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    # 1.项目必须存在
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2.删除并落库
    session.delete(project)
    session.commit()

    # 3.统一结果集返回
    return Result.success(message="删除成功")
