# app/auth/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .security import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth-鉴权"])

# 模拟数据库中的超级管理员账号（实际生产需从 users 表查询）
FAKE_ADMIN_DB = {
    "YiPack_admin": {
        "username": "YiPack_admin",
        # 密码 "YiPack_admin_pwd" 的 bcrypt 哈希值
        "hashed_password": "$2b$12$K.z8u.t.G6/Hj... (这里省略完整哈希，需通过 get_password_hash 生成)",
        "role": "super_admin"
    }
}


@router.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    员工/管理员登录接口：颁发 JWT
    """
    user_dict = FAKE_ADMIN_DB.get(form_data.username)
    # 验证账号和密码（此处为了打样，暂用明文比对演示，生产必须用 verify_password）
    if not user_dict or form_data.password != "YiPack_admin_pwd":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user_dict["username"], "role": user_dict["role"]}
    )
    # 返回标准的 OAuth2 响应格式
    return {"access_token": access_token, "token_type": "bearer"}