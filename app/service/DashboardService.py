from datetime import date, datetime, timedelta, time

from sqlmodel import Session, func, select

from app.common.Result import Result
from app.models.Category import Category
from app.models.Comment import Comment
from app.models.Message import Message
from app.models.Post import Post
from app.models.Tag import Tag
from app.models.Visitor import Visitor
from app.schemas.DashboardSchemas import (
    DashboardCountResponse,
    DashboardNamedValue,
    DashboardStatsResponse,
    DashboardTrendItem,
)


def _fill_trend(start: date, counts_by_day: dict[str, int]) -> list[DashboardTrendItem]:
    """从 start 起连续 30 天，缺日补 0。"""
    items: list[DashboardTrendItem] = []
    for offset in range(30):
        day = start + timedelta(days=offset)
        key = day.isoformat()
        items.append(DashboardTrendItem(date=key, count=counts_by_day.get(key, 0)))
    return items


def get_dashboard_stats(session: Session) -> Result:
    """聚合仪表盘：计数、近 30 天趋势、分类与浏览器分布。

    Args:
        session: 数据库会话，由路由传入。

    Returns:
        统一结果集。成功时 code=200，data 为仪表盘统计。
    """
    # 1.各模块计数
    posts = session.exec(
        select(func.count(Post.id)).where(Post.status == "published")
    ).one()
    drafts = session.exec(
        select(func.count(Post.id)).where(Post.status == "draft")
    ).one()
    categories = session.exec(select(func.count(Category.id))).one()
    tags = session.exec(select(func.count(Tag.id))).one()
    comments = session.exec(select(func.count(Comment.id))).one()
    messages = session.exec(select(func.count(Message.id))).one()
    visitors = session.exec(select(func.count(Visitor.id))).one()

    # 2.近 30 天窗口（含今天，共 30 个日期）
    today = date.today()
    start = today - timedelta(days=29)
    start_dt = datetime.combine(start, time.min)

    # 3.已发布文章按 published_at 日期分组
    post_day = func.date(Post.published_at)
    post_rows = session.exec(
        select(post_day, func.count(Post.id))
        .where(
            Post.status == "published",
            Post.published_at.is_not(None),
            Post.published_at >= start_dt,
        )
        .group_by(post_day)
    ).all()
    post_counts: dict[str, int] = {}
    for day_value, count in post_rows:
        if day_value is None:
            continue
        key = day_value.isoformat() if hasattr(day_value, "isoformat") else str(day_value)
        post_counts[key[:10]] = int(count or 0)

    # 4.访客按 created_at 日期分组
    visitor_day = func.date(Visitor.created_at)
    visitor_rows = session.exec(
        select(visitor_day, func.count(Visitor.id))
        .where(Visitor.created_at >= start_dt)
        .group_by(visitor_day)
    ).all()
    visitor_counts: dict[str, int] = {}
    for day_value, count in visitor_rows:
        if day_value is None:
            continue
        key = day_value.isoformat() if hasattr(day_value, "isoformat") else str(day_value)
        visitor_counts[key[:10]] = int(count or 0)

    # 5.有文章的分类分布
    cat_rows = list(
        session.exec(
            select(Category)
            .where(Category.post_count > 0)
            .order_by(Category.sort)
        ).all()
    )
    category_distribution = [
        DashboardNamedValue(name=row.name, value=row.post_count) for row in cat_rows
    ]

    # 6.浏览器分布；空显示「未知」
    browser_rows = session.exec(
        select(Visitor.browser, func.count(Visitor.id)).group_by(Visitor.browser)
    ).all()
    browser_distribution = [
        DashboardNamedValue(name=(name or "未知"), value=int(count or 0))
        for name, count in browser_rows
    ]

    # 7.统一结果集返回
    return Result.success(
        DashboardStatsResponse(
            counts=DashboardCountResponse(
                posts=int(posts or 0),
                drafts=int(drafts or 0),
                categories=int(categories or 0),
                tags=int(tags or 0),
                comments=int(comments or 0),
                messages=int(messages or 0),
                visitors=int(visitors or 0),
            ),
            post_trend=_fill_trend(start, post_counts),
            visitor_trend=_fill_trend(start, visitor_counts),
            category_distribution=category_distribution,
            browser_distribution=browser_distribution,
        )
    )
