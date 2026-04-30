# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.redis import redis_client
from app.core.exceptions import BusinessLogicError, business_logic_exception_handler
from app.database import engine, Base

from app.auth.routes import router as auth_router
from app.cms.routes import router as cms_router
from app.erp.routes import router as erp_router


# --- 生命周期管理 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 启动时：连接数据库并建表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("====== 益发包装 MySQL 数据库表同步完成 ======")

    # 2. 测试 Redis 连接
    try:
        ping = await redis_client.ping()
        if ping:
            print("====== 益发包装 Redis 缓存连接成功 ======")
    except Exception as e:
        print(f"Redis 连接失败: {e}")

    yield  # 应用在此处运行

    # 3. 关闭时：清理资源
    await engine.dispose()
    await redis_client.aclose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="CMS 官网内容分发 + ERP 制造执行核心",
    version=settings.VERSION,
    lifespan=lifespan  # 注册生命周期
)

# 注册全局异常处理器
app.add_exception_handler(BusinessLogicError, business_logic_exception_handler)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件挂载
os.makedirs("app/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 注册路由
app.include_router(auth_router)
app.include_router(cms_router)
app.include_router(erp_router)


@app.get("/", tags=["Health Check"])
async def root():
    return {"message": f"{settings.PROJECT_NAME} API 运行正常", "docs": "/docs"}