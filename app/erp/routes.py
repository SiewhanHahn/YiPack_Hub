# app/erp/routes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from app.database import get_async_db
from app.erp import schemas, services, models
from app.auth.dependencies import get_current_user, require_roles
from app.auth.models import User

router = APIRouter(prefix="/api/erp", tags=["ERP-生产执行层"])

# ==========================================
# 1. 产品档案管理 (BOM)
# ==========================================
@router.post("/products", response_model=schemas.ProductResponse)
async def create_product(
        product: schemas.ProductCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(require_roles(["super_admin", "manager"])) # 仅管理层可修改BOM
):
    """录入新产品，必须包含理论单品克重（红线指标）"""
    new_product = models.Product(**product.model_dump())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

@router.get("/products", response_model=List[schemas.ProductResponse])
async def list_products(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user) # 登录员工可见
):
    """获取产品列表"""
    result = await db.execute(select(models.Product))
    return result.scalars().all()


# ==========================================
# 2. 生产工单管理 (MES)
# ==========================================
@router.post("/orders", response_model=schemas.WorkOrderResponse)
async def create_work_order(
        order: schemas.WorkOrderCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(require_roles(["super_admin", "manager"])) # 仅管理层可下发工单
):
    """下发生产工单，绑定产品与计划产量"""
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
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user) # 操作工可流转工单
):
    """
    【核心流转接口】推进工单状态。内置食品安全熟化期拦截与损耗数据校验。
    """
    updated_order = await services.advance_order_status(db, order_id, schema)
    return updated_order


# ==========================================
# 3. 车间数字化看板 (Dashboard - MySQL 实时聚合)
# ==========================================
@router.get("/dashboard/summary")
async def get_dashboard_summary(
        db: AsyncSession = Depends(get_async_db),
        current_user: User = Depends(get_current_user)
):
    """
    获取数字化大屏核心指标（由 MySQL 联合索引支撑实时聚合计算）
    """
    # 1. 获取各工序在制品数量 (WIP)
    wip_result = await db.execute(
        select(models.WorkOrder.status, func.count(models.WorkOrder.id))
        .where(models.WorkOrder.status != "Completed")
        .group_by(models.WorkOrder.status)
    )
    wip_data = {row[0]: row[1] for row in wip_result.all()}

    # 2. 获取已结案工单的汇总效能数据（总产出、平均废品率）
    metrics_result = await db.execute(
        select(
            func.sum(models.WorkOrder.actual_output_pcs).label("total_output"),
            func.avg(models.WorkOrder.scrap_rate_percent).label("avg_scrap_rate")
        ).where(models.WorkOrder.status == "Completed")
    )
    metrics = metrics_result.one()

    return {
        "status": "success",
        "timestamp": datetime.now(timezone.utc),
        "data": {
            "wip_distribution": wip_data, # 例: {"Printing": 2, "Curing": 5}
            "production_metrics": {
                "total_completed_pcs": int(metrics.total_output or 0),
                "average_scrap_rate_percent": round(metrics.avg_scrap_rate or 0.0, 2)
            }
        }
    }