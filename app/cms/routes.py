# app/cms/routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_async_db
from app.auth.security import oauth2_scheme  # 引入鉴权依赖
from app.core.exceptions import BusinessLogicError
from .models import CompanyContent
from .schemas import ContentCreate, ContentUpdate, ContentResponse

router = APIRouter(prefix="/api/cms", tags=["CMS-官网与内容管理"])


# ==========================================
# 前台公开接口 (无需鉴权)
# ==========================================
@router.get("/public/contents/{content_type}", response_model=dict)
async def get_public_content(content_type: str, db: AsyncSession = Depends(get_async_db)):
    """
    【无需鉴权】获取官网展示内容，供 Vue 前台直接调用。
    例如调用 /api/cms/public/contents/product 获取所有上架的包装袋展示。
    """
    result = await db.execute(
        select(CompanyContent)
        .where(CompanyContent.content_type == content_type)
        .where(CompanyContent.is_active == True)
        .order_by(CompanyContent.created_at.desc())
    )
    contents = result.scalars().all()

    return {
        "status": "success",
        "data": [
            {
                "id": c.id,
                "title": c.title,
                "image_url": c.image_url,
                "content_text": c.content_text
            } for c in contents
        ]
    }


# ==========================================
# 后台管理接口 (必须携带 Token 鉴权)
# ==========================================
@router.post("/admin/contents", response_model=ContentResponse)
async def create_content(
        content: ContentCreate,
        db: AsyncSession = Depends(get_async_db),
        token: str = Depends(oauth2_scheme)  # 安全防线：验证 JWT
):
    """发布新的官网内容（如上传新的企业资质、新增产品）"""
    new_content = CompanyContent(**content.model_dump())
    db.add(new_content)
    await db.commit()
    await db.refresh(new_content)
    return new_content


@router.put("/admin/contents/{content_id}", response_model=ContentResponse)
async def update_content(
        content_id: int,
        content_update: ContentUpdate,
        db: AsyncSession = Depends(get_async_db),
        token: str = Depends(oauth2_scheme)
):
    """修改内容或进行下架操作 (修改 is_active)"""
    result = await db.execute(select(CompanyContent).where(CompanyContent.id == content_id))
    content_obj = result.scalar_one_or_none()

    if not content_obj:
        raise BusinessLogicError("CMS内容不存在", status_code=404)

    update_data = content_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(content_obj, key, value)

    await db.commit()
    await db.refresh(content_obj)
    return content_obj