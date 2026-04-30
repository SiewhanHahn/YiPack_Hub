# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    全局环境变量强类型配置类
    应用启动时会自动寻找 .env 文件并进行类型校验
    """
    PROJECT_NAME: str = "定远县益发包装科技 ERP 系统"
    VERSION: str = "1.0.0"

    # --- 数据库配置 ---
    DB_HOST: str
    DB_PORT: int = 3307
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # --- Redis 缓存配置 ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6380

    # --- JWT 安全鉴权配置 ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Pydantic V2 配置字典
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # 忽略 .env 中多余的 Docker 专用变量（如 MYSQL_ROOT_PASSWORD）
    )

# 实例化全局单例，供其他模块引入
settings = Settings()