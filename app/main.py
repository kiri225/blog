from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.Config import CORS_ORIGINS, UPLOADS_DIR
from app.api.router import api_router
from app.Database import init_db
from app.common.ExceptionHub import register_exception_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行一次，初始化数据库
    init_db()
    yield


# 创建 FastAPI 应用（docs 地址是 /docs）
app = FastAPI(title="kiri blog backend", version="0.1.0", lifespan=lifespan)
register_exception_handlers(app)

# 挂载路由
app.include_router(api_router)


# 添加 CORS 中间件
app.add_middleware(
    # 
    CORSMiddleware,
    # 允许的来源
    allow_origins=CORS_ORIGINS,
    # 允许凭证
    allow_credentials=True,
    # 允许的方法
    allow_methods=["*"],
    # 允许的请求头
    allow_headers=["*"],
)

# 挂载上传目录
UPLOADS_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# 健康检查
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# 获取路由
@app.get("/api/routes")
async def get_routes():
    return {"code": 200, "message": "success", "data": []}