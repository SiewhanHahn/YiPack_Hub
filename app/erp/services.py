# app/erp/services.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from .models import WorkOrder
from .schemas import WorkOrderAdvance


async def get_order_by_id_with_product(db: AsyncSession, order_id: int) -> WorkOrder:
    """关联查询出工单及对应的产品BOM信息，用于克重计算"""
    result = await db.execute(
        select(WorkOrder).options(selectinload(WorkOrder.product)).where(WorkOrder.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    return order


async def advance_order_status(db: AsyncSession, order_id: int, schema: WorkOrderAdvance) -> WorkOrder:
    """
    流转工单状态并执行业务红线校验与损耗核算
    """
    order = await get_order_by_id_with_product(db, order_id)

    # 【业务红线 1】：熟化期强制锁定 (Time Lock)
    if order.status == "Curing" and schema.next_status in ["Slitting", "BagMaking"]:
        if not order.curing_start_at:
            raise HTTPException(status_code=400, detail="异常：熟化开始时间未记录")

        release_time = order.curing_start_at + timedelta(hours=order.curing_duration_hours)
        current_time = datetime.now(timezone.utc)

        if current_time < release_time:
            diff = release_time - current_time
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"【安全拦截】批次处于熟化锁定中，剩余时间: {diff.seconds // 3600}小时。禁止进入下一工序！"
            )

    # 如果刚进入熟化期，打上时间戳
    if schema.next_status == "Curing" and order.status != "Curing":
        order.curing_start_at = datetime.now(timezone.utc)

    # 【业务红线 2】：结案时核算损耗闭环计算 (Loss Tracking)
    if schema.next_status == "Completed":
        if schema.raw_material_input_kg is None or schema.actual_output_pcs is None:
            raise HTTPException(status_code=400, detail="结案必须录入实际耗材总重与实际合格数")

        if schema.raw_material_input_kg <= 0:
            raise HTTPException(status_code=400, detail="耗材录入不能小于等于 0")

        order.raw_material_input_kg = schema.raw_material_input_kg
        order.actual_output_pcs = schema.actual_output_pcs

        # 核心物料转换计算：理论需要耗用的原料重量 (公斤 = 个数 * 单品克重 / 1000)
        theoretical_weight_kg = (schema.actual_output_pcs * order.product.unit_weight_gram) / 1000.0

        # 计算废料重量与废品率 (实际耗用 - 理论耗用)
        waste_weight_kg = order.raw_material_input_kg - theoretical_weight_kg

        # 容错处理：理论上存在极小概率的负偏差（称重误差），下限截断至 0
        waste_weight_kg = max(waste_weight_kg, 0)
        scrap_rate = (waste_weight_kg / order.raw_material_input_kg) * 100

        order.waste_weight_kg = round(waste_weight_kg, 2)
        order.scrap_rate_percent = round(scrap_rate, 2)

    order.status = schema.next_status
    await db.commit()
    await db.refresh(order)
    return order