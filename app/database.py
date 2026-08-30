from sqlmodel import SQLModel, create_engine, Session
from app.config import DATABASE_URL
import app.models  # 触发 __init__ 导入，把各表登记进 metadata

# 创建数据库引擎
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# 初始化数据库
def init_db():
    SQLModel.metadata.create_all(engine)

# 获取数据库会话
def get_session():
    with Session(engine) as session:
        yield session