# app/core/redis.py
import redis.asyncio as redis
from app.core.config import settings

# 建立异步 Redis 连接池
# decode_responses=True 确保我们取出的数据直接是字符串(str)而不是字节(bytes)
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True,
    max_connections=10
)

async def get_redis():
    """FastAPI 依赖注入：获取 Redis 实例"""
    try:
        yield redis_client
    finally:
        # Redis 连接池会自动管理回收，这里无需显式 close()
        pass