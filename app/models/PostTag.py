from __future__ import annotations

from sqlalchemy import Index
from sqlmodel import SQLModel, Field


class PostTag(SQLModel, table=True):
    """文章与标签的多对多中间表。联合主键，删文章/标签时级联删除关联行。"""

    # 类名 PostTag 小写是 posttag，与库表 post_tag 不一致，必须显式指定
    __tablename__ = "post_tag"  # pyright: ignore[reportAssignmentType]

    # 文章 ID，外键 post.id；联合主键最左列，按文章查标签已能走主键
    post_id: int = Field(foreign_key="post.id", primary_key=True)
    # 标签 ID，外键 tag.id
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)

    __table_args__ = (
        # 按标签筛文章：WHERE tag_id=? 取 post_id；主键是 (post_id, tag_id)，反向查需要这支
        Index("idx_post_tag_tag", "tag_id", "post_id"),
    )
