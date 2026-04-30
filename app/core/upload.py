# app/core/upload.py
import os
import uuid
from fastapi import UploadFile
from aiofiles import open as aio_open  # pip install aiofiles

UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_upload_file(file: UploadFile) -> str:
    """
    异步保存上传的文件，返回相对路径。
    使用 UUID 重命名防止文件名冲突。
    """
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    async with aio_open(file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)

    return f"/static/uploads/{unique_filename}"