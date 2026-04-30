# app/cms/routes.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_async_db
from .models import CompanyContent

router = APIRouter(prefix="/api/cms", tags=["CMS-官网前台展示"])


@router.get("/public/contents/{content_type}")
async def get_public_content(content_type: str, db: AsyncSession = Depends(get_async_db)):
    """
    【无需鉴权】获取官网展示内容，供 Vue 前台直接调用
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