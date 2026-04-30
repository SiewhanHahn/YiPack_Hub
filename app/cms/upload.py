# app/cms/upload.py
import os
from fastapi import APIRouter, Depends, UploadFile, File
from app.auth.security import oauth2_scheme
from app.core.exceptions import BusinessLogicError
from app.core.upload import save_upload_file

router = APIRouter(prefix="/api/upload", tags=["公共服务-文件上传"])

# 安全红线配置
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
# 限制最大文件大小：5MB (为了保护本地磁盘和网络带宽)
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/image")
async def upload_image(
        file: UploadFile = File(..., description="前端表单上传的图片文件"),
        token: str = Depends(oauth2_scheme)  # 【安全红线】绝对禁止匿名上传，必须携带 JWT
):
    """
    通用图片上传接口 (供 Vue 3 的 el-upload 等组件调用)
    返回相对路径 URL，前端拿到后可直接存入 CMS 对应表单。
    """
    # 1. 提取文件后缀并转为小写
    file_ext = os.path.splitext(file.filename)[1].lower()

    # 2. 【安全校验 1】文件类型白名单防御
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise BusinessLogicError(
            f"不支持的文件格式: {file_ext}。仅支持 JPG, PNG, WEBP, GIF。",
            status_code=400
        )

    # 3. 【安全校验 2】文件大小防御 (使用 file.size, 需 FastAPI 0.104+ / Python-multipart)
    # 注意：读取整个文件到内存会影响高并发，这里用 seek() 快速获取大小
    await file.seek(0, 2)  # 移动指针到文件末尾
    file_size = file.file.tell()  # 获取指针位置（即文件字节数）
    await file.seek(0)  # 务必将指针重置回开头，否则后面 save_upload_file 会读出空文件

    if file_size > MAX_FILE_SIZE:
        raise BusinessLogicError(
            "文件过大，为了节省带宽，请上传不超过 5MB 的图片。",
            status_code=413  # Payload Too Large
        )

    # 4. 调用已有的底层核心存储方法 (app/core/upload.py)
    # 内部会自动生成 UUID 防止文件名冲突，并异步写入磁盘
    file_url = await save_upload_file(file)

    return {
        "status": "success",
        "message": "上传成功",
        "data": {
            "url": file_url,  # 例如: "/static/uploads/uuid-xxx.jpg"
            "filename": file.filename,  # 原始文件名
            "size": file_size  # 文件字节数
        }
    }