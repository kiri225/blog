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

# 创建数据库引擎
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# 初始化数据库
def init_db():
    SQLModel.metadata.create_all(engine)

# 获取数据库会话
def get_session():
    with Session(engine) as session:
        yield session
