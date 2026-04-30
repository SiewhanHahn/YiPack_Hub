# app/core/logging.py
import logging
import sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app_runtime.log") # 持久化到本地文件
        ],
    )
    # 减少 SQLAlchemy 冗余的 INFO 日志
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

logger = logging.getLogger("YiPack_API")