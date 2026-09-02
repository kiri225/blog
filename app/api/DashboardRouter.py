from fastapi import Depends
from fastapi.routing import APIRouter
from sqlmodel import Session

from app.Deps import get_session
from app.common.Result import Result
from app.schemas.DashboardSchemas import DashboardStatsResponse
from app.service import DashboardService as dashboard_service


router = APIRouter(prefix="/api/dashboard", tags=["仪表盘"])


@router.get("/stats", response_model=Result[DashboardStatsResponse])
def get_dashboard_stats(session: Session = Depends(get_session)):
    """仪表盘聚合统计。

    公开接口。counts、近 30 天文章/访客趋势（缺日补 0）、分类与浏览器分布。

    Args:
        session: 数据库会话，由依赖注入提供。

    Returns:
        统一结果集。成功时 code=200，data 为仪表盘统计。
    """
    return dashboard_service.get_dashboard_stats(session)
