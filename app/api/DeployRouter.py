from fastapi import Depends
from fastapi.routing import APIRouter

from app.Deps import get_current_user
from app.common.Result import Result
from app.service import DeployService as deploy_service


router = APIRouter(prefix="/api/system", tags=["系统"])


@router.post("/deploy", response_model=Result[dict])
def trigger_deploy(current_user: dict = Depends(get_current_user)):
    """拉取 GitHub 最新代码并重新构建部署三个服务（需管理员登录）。"""
    return deploy_service.trigger_deploy()


@router.get("/deploy/status", response_model=Result[dict])
def deploy_status(current_user: dict = Depends(get_current_user)):
    """查询部署任务是否仍在执行。"""
    return deploy_service.get_deploy_status()
