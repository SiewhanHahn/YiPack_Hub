# app/core/exceptions.py
from fastapi import Request, status
from fastapi.responses import JSONResponse

class BusinessLogicError(Exception):
    """通用业务逻辑异常类（如熟化期未满强行流转）"""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.detail = detail
        self.status_code = status_code

async def business_logic_exception_handler(request: Request, exc: BusinessLogicError):
    """
    拦截 BusinessLogicError，转换为标准 JSON 返回前端
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "type": "BusinessLogicError",
            "path": request.url.path
        },
    )