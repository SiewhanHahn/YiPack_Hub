# app/erp/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# --- Product ---
class ProductBase(BaseModel):
    name: str = Field(..., max_length=100, description="产品名称")
    material_spec: str = Field(..., max_length=200, description="材质结构")
    unit_weight_gram: float = Field(..., gt=0, description="单品理论克重(g)")
    description: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)  # 适配 SQLAlchemy 模型


# --- Work Order ---
class WorkOrderCreate(BaseModel):
    order_no: str
    product_id: int
    target_pcs: int = Field(..., gt=0)
    curing_duration_hours: int = Field(default=48, description="自定义熟化要求时长")


class WorkOrderAdvance(BaseModel):
    """工单流转参数，用于向下一工序推进"""
    next_status: str

    # 若此时结案，需提交实际损耗参数
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
    model_config = ConfigDict(from_attributes=True)