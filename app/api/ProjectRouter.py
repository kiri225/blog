from fastapi import Depends
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_current_user, get_session
from app.common.Result import Result
from app.schemas.ProjectSchemas import (
    CreateProjectRequest,
    ProjectResponse,
    UpdateProjectRequest,
)
from app.service import ProjectService as project_service


router = APIRouter(prefix="/api/projects", tags=["项目"])


@router.get("", response_model=Result[list[ProjectResponse]])
def list_projects(session: Session = Depends(get_session)):
    """获取项目列表。

    公开接口。按 sort 升序返回全部项目。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为项目列表。
    """
    return project_service.list_projects(session)


@router.post("", response_model=Result[ProjectResponse])
def create_project(
    CreateProjectReq: CreateProjectRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """创建项目。

    需管理员 JWT。slug 全站唯一，冲突则 400。
    status 仅允许 developing / active / archived。

    Args:
        CreateProjectReq: 创建项目请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为项目。
    """
    return project_service.create_project(session, CreateProjectReq)


@router.get("/{slug}", response_model=Result[ProjectResponse])
def get_project(slug: str, session: Session = Depends(get_session)):
    """按 slug 获取项目详情。

    公开接口。不存在则 404。须写在静态路径之后。

    Args:
        slug: 项目 URL 别名。
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为项目。
    """
    return project_service.get_project_by_slug(session, slug)


@router.put("/{project_id}", response_model=Result[ProjectResponse])
def update_project(
    project_id: int,
    UpdateProjectReq: UpdateProjectRequest,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """更新项目。

    需管理员 JWT。路径用主键 id，不是 slug。全部字段可选。
    项目不存在则 404。slug 冲突则 400。

    Args:
        project_id: 项目 ID。
        UpdateProjectReq: 更新项目请求体。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，data 为项目。
    """
    return project_service.update_project(session, project_id, UpdateProjectReq)


@router.delete("/{project_id}", response_model=Result)
def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user),
):
    """删除项目。

    需管理员 JWT。路径用主键 id。项目不存在则 404。

    Args:
        project_id: 项目 ID。
        session: 数据库会话，由依赖注入提供。
        current_user: JWT payload，用来校验已登录；本接口不用里面的字段。

    Returns:
        统一结果集。成功时 code=200，message 为「删除成功」。
    """
    return project_service.delete_project(session, project_id)
