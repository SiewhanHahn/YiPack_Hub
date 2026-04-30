# app/cms/models.py
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.database import Base


class CompanyContent(Base):
    """企业官网 CMS 内容表"""
    __tablename__ = "cms_company_contents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 内容归类，极其重要。根据设计图可分为：
    # 'certificate'(资质), 'profile'(简介), 'business'(主营),
    # 'equipment'(装备), 'environment'(环保), 'product'(产品展示)
    content_type: Mapped[str] = mapped_column(String(50), index=True, comment="内容分类标识")

    title: Mapped[str] = mapped_column(String(100), comment="标题（如：营业执照、八边封袋）")

    # 图片通常是企业官网的核心（如产品图、车间图、资质证书）
    image_url: Mapped[str | None] = mapped_column(String(255), comment="相对路径的图片地址")

    # 针对“公司简介”或“环保与安全管理”这种大段落文本
    content_text: Mapped[str | None] = mapped_column(Text, comment="图文详细内容")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否在前台展示（软删除/上下架控制）")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                                 onupdate=lambda: datetime.now(timezone.utc))