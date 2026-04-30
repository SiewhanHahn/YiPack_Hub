# app/erp/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ... (ProductBase, ProductCreate, ProductResponse 保持不变) ...

class WorkOrderCreate(BaseModel):
    order_no: str
    product_id: int
    target_pcs: int = Field(..., gt=0)
    curing_duration_hours: int = Field(default=48, description="自定义熟化要求时长")


class WorkOrderAdvance(BaseModel):
    next_status: str
    actual_output_pcs: Optional[int] = None
    raw_material_input_kg: Optional[float] = None


class WorkOrderResponse(BaseModel):
    id: int
    order_no: str
    product_id: int
    status: str
    target_pcs: int
    curing_start_at: Optional[datetime]
    created_at: datetime
    # [修复]: 暴露给前端的字段
    raw_material_input_kg: float
    actual_output_pcs: int
    waste_rate_percent: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)