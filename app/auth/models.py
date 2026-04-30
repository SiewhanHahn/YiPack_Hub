# app/auth/models.py
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "sys_users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, comment="登录账号")
    hashed_password: Mapped[str] = mapped_column(String(255), comment="Bcrypt加密密码")
    full_name: Mapped[str] = mapped_column(String(50), comment="员工真实姓名")

    # 角色区分：super_admin(超管), manager(厂长), operator(车间操作工)
    role: Mapped[str] = mapped_column(String(20), default="operator")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))