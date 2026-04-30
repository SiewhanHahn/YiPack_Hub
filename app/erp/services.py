# app/erp/services.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from .models import WorkOrder, Product
from .schemas import WorkOrderAdvance


async def get_order_by_id(db: AsyncSession, order_id: int) -> WorkOrder:
    result = await db.execute(select(WorkOrder).where(WorkOrder.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="工单不存在")
    return order


async def advance_order_status(db: AsyncSession, order_id: int, schema: WorkOrderAdvance):
    """
    流转工单状态并执行业务红线校验
    """
    order = await get_order_by_id(db, order_id)

    # 【业务红线 1】：熟化期强制锁定 (Time Lock)
    # 如果当前状态是熟化中 (Curing)，且试图离开该状态（流向分切或制袋）
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

    # 业务逻辑：如果刚进入熟化期，打上时间戳
    if schema.next_status == "Curing" and order.status != "Curing":
        order.curing_start_at = datetime.now(timezone.utc)

    # 【业务红线 2】：结案时核算损耗 (Loss Tracking)
    if schema.next_status == "Completed":
        if schema.raw_material_input_kg is None or schema.actual_output_pcs is None:
            raise HTTPException(status_code=400, detail="结案必须录入实际耗材总重与实际合格数")

        order.raw_material_input_kg = schema.raw_material_input_kg
        order.actual_output_pcs = schema.actual_output_pcs

        # 预留：此处可触发后台 Celery/Redis 任务计算废品率并推送到看板面板

    order.status = schema.next_status
    await db.commit()
    await db.refresh(order)
    return order