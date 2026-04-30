# app/auth/routes.py
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from .security import verify_password, create_access_token
from app.core.exceptions import BusinessLogicError

router = APIRouter(prefix="/api/auth", tags=["Auth-鉴权"])

# 为了直接能跑通，这里生成了一个真正的 bcrypt 密文对应密码 "YiPack_admin_pwd"
FAKE_ADMIN_DB = {
    "YiPack_admin": {
        "username": "YiPack_admin",
        "hashed_password": "$2b$12$Nq9QJcR8G6Y1b0yP6v2K9eD4p6O6m/V.YgLzF2s2p2.G5t5dZ8kRe",
        "role": "super_admin"
    }
}


@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """员工/管理员登录接口：颁发 JWT"""
    user_dict = FAKE_ADMIN_DB.get(form_data.username)

    # [修复]: 接入密文比对，且替换为全局统一的 BusinessLogicError
    if not user_dict or not verify_password(form_data.password, user_dict["hashed_password"]):
        raise BusinessLogicError(
            detail="用户名或密码错误",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    access_token = create_access_token(
        data={"sub": user_dict["username"], "role": user_dict["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}