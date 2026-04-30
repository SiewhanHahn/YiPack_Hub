# app/erp/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from app.database import get_async_db
from app.erp import schemas, services, models

# 如果需要权限控制，可以引入 auth 依赖
# from app.auth.security import oauth2_scheme

router = APIRouter(prefix="/api/erp", tags=["ERP-生产执行层"])


# ==========================================
# 1. 产品档案管理 (BOM)
# ==========================================
@router.post("/products", response_model=schemas.ProductResponse)
async def create_product(
        product: schemas.ProductCreate,
        db: AsyncSession = Depends(get_async_db)
        # token: str = Depends(oauth2_scheme) # 生产环境需开启鉴权
):
    """录入新产品，必须包含理论单品克重（红线指标）"""
    new_product = models.Product(**product.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


@router.get("/products", response_model=List[schemas.ProductResponse])
async def list_products(db: AsyncSession = Depends(get_async_db)):
    """获取产品列表"""
    result = await db.execute(select(models.Product))
    return result.scalars().all()


# ==========================================
# 2. 生产工单管理 (MES)
# ==========================================
@router.post("/orders", response_model=schemas.WorkOrderResponse)
async def create_work_order(
        order: schemas.WorkOrderCreate,
        db: AsyncSession = Depends(get_async_db)
):
    """下达生产工单，绑定产品与计划产量"""
    # 校验产品是否存在
    prod_check = await db.execute(select(models.Product).where(models.Product.id == order.product_id))
    if not prod_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="绑定的产品ID不存在")

    new_order = models.WorkOrder(**order.model_dump())
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    return new_order


@router.post("/orders/{order_id}/advance", response_model=schemas.WorkOrderResponse)
async def advance_work_order(
        order_id: int,
        schema: schemas.WorkOrderAdvance,
        db: AsyncSession = Depends(get_async_db)
):
    """
    【核心流转接口】
    推进工单状态。内置食品安全熟化期拦截与损耗数据校验。
    """
    updated_order = await services.advance_order_status(db, order_id, schema)
    return updated_order


# ==========================================
# 3. 车间数字化看板 (Dashboard)
# ==========================================
@router.get("/dashboard/wip")
async def get_wip_dashboard(db: AsyncSession = Depends(get_async_db)):
    """
    获取当前各工序的在制品 (Work In Progress) 统计数据。
    后续优化：此处可结合 Redis 进行缓存，降低高并发刷看板对 MySQL 的压力。
    """
    result = await db.execute(
        select(models.WorkOrder.status, func.count(models.WorkOrder.id))
        .group_by(models.WorkOrder.status)
    )

    # 将查询结果转换为字典，例如: {"Printing": 2, "Curing": 5}
    wip_data = {row[0]: row[1] for row in result.all()}

    return {
        "status": "success",
        "timestamp": func.now(),
        "data": wip_data
    }