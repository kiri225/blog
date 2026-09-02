from __future__ import annotations

from pydantic import BaseModel


class DashboardCountResponse(BaseModel):
    """仪表盘计数响应体。"""

    # 已发布文章数
    posts: int = 0
    # 草稿文章数
    drafts: int = 0
    # 分类数
    categories: int = 0
    # 标签数
    tags: int = 0
    # 评论数（全表）
    comments: int = 0
    # 留言数（全表）
    messages: int = 0
    # 访客记录数（不去重）
    visitors: int = 0


class DashboardTrendItem(BaseModel):
    """按日趋势一项。"""

    # 日期 YYYY-MM-DD
    date: str
    # 当天数量，无数据为 0
    count: int = 0


class DashboardNamedValue(BaseModel):
    """名称 + 数值，用于分布图。"""

    # 名称
    name: str
    # 数值
    value: int = 0


class DashboardStatsResponse(BaseModel):
    """仪表盘统计响应体。"""

    # 各模块计数
    counts: DashboardCountResponse
    # 近 30 天已发布文章趋势，长度恒为 30
    post_trend: list[DashboardTrendItem]
    # 近 30 天访客趋势，长度恒为 30
    visitor_trend: list[DashboardTrendItem]
    # 有文章的分类分布
    category_distribution: list[DashboardNamedValue]
    # 浏览器分布；空浏览器显示为「未知」
    browser_distribution: list[DashboardNamedValue]
