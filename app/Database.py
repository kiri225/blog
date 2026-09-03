from sqlalchemy import text
from sqlmodel import SQLModel, create_engine, Session
from app.Config import DATABASE_URL
# 导入各表，把映射登记进 SQLModel.metadata，create_all 才能建出表
from app.models.User import User
from app.models.Category import Category
from app.models.Tag import Tag
from app.models.Post import Post
from app.models.PostTag import PostTag
from app.models.GitHubUser import GitHubUser
from app.models.Comment import Comment
from app.models.Message import Message
from app.models.Chatter import Chatter
from app.models.ChatterComment import ChatterComment
from app.models.Album import Album
from app.models.Photo import Photo
from app.models.Project import Project
from app.models.FriendLink import FriendLink
from app.models.SiteConfig import SiteConfig
from app.models.BookmarkCategory import BookmarkCategory
from app.models.BookmarkSite import BookmarkSite
from app.models.Visitor import Visitor


# 创建数据库引擎
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# 已被组合索引替代、或与 UNIQUE 重复的旧索引（不含唯一约束）
_OBSOLETE_INDEXES = (
    "idx_post_slug",
    "idx_post_status",
    "idx_github_user_id",
    "idx_comment_post",
    "idx_comment_status",
    "idx_message_status",
    "idx_message_parent",
    "idx_chatter_status",
    "idx_chatter_comment_chatter",
    "idx_chatter_comment_status",
    "idx_photo_album",
    "idx_bookmark_site_category",
    "ix_post_status",
    "ix_comment_post_id",
    "ix_comment_github_user_id",
    "ix_comment_status",
    "ix_message_github_user_id",
    "ix_message_parent_id",
    "ix_message_status",
    "ix_chatter_status",
    "ix_chatter_comment_chatter_id",
    "ix_chatter_comment_github_user_id",
    "ix_chatter_comment_status",
    "ix_photo_album_id",
    "ix_friend_link_is_approved",
    "ix_bookmark_site_category_id",
    "ix_visitor_ip",
    "ix_visitor_created_at",
)


def ensure_indexes() -> None:
    """按模型补齐索引。

    create_all 只建缺失的表，已存在的表不会补 Index。
    先删掉已替换的旧单列索引，再按 metadata 建新索引；同名则跳过。
    """
    with engine.begin() as conn:
        for name in _OBSOLETE_INDEXES:
            conn.execute(text(f"DROP INDEX IF EXISTS {name}"))
        for table in SQLModel.metadata.tables.values():
            for index in table.indexes:
                index.create(conn, checkfirst=True)


# 初始化数据库
def init_db():
    SQLModel.metadata.create_all(engine)
    ensure_indexes()
    from app.service.SiteConfigService import seed_site_configs

    with Session(engine) as session:
        seed_site_configs(session)

# 获取数据库会话
def get_session():
    with Session(engine) as session:
        yield session
