# app/database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from dotenv import load_dotenv

load_dotenv()

# 构建异步 MySQL 连接 URL (使用 aiomysql 驱动)
# 注意这里从 .env 读取的依然是 3307 端口和 YiPack_xxx 命名
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

ASYNC_SQLALCHEMY_DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# 创建异步引擎
engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    echo=False,          # 生产环境关闭 SQL 回显
    pool_pre_ping=True,  # 悲观连接池检查，防止 MySQL 失去连接
    pool_size=20,
    max_overflow=30
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False, # 异步环境下必须设为 False，避免会话结束后属性过期
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

# FastAPI 依赖项：获取异步数据库会话
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()