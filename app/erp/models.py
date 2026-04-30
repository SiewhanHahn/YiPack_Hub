# app/erp/models.py
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from app.database import Base


class Product(Base):
    __tablename__ = "erp_products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    material_spec: Mapped[str] = mapped_column(String(200))

    # 核心红线：理论单品克重
    unit_weight_gram: Mapped[float] = mapped_column(Float, comment="单品理论克重(g)")
    description: Mapped[str | None] = mapped_column(Text)

    # 关联
    orders: Mapped[list["WorkOrder"]] = relationship("WorkOrder", back_populates="product",
                                                     cascade="all, delete-orphan")


class WorkOrder(Base):
    __tablename__ = "erp_work_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_no: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("erp_products.id"))

    target_pcs: Mapped[int] = mapped_column(Integer, comment="计划产出数量(pcs)")

    # 损耗追踪闭环
    raw_material_input_kg: Mapped[float] = mapped_column(Float, default=0.0)
    actual_output_pcs: Mapped[int] = mapped_column(Integer, default=0)

    # 状态机：Pending, Printing, Laminating, Curing, Slitting, BagMaking, Completed
    status: Mapped[str] = mapped_column(String(20), default="Pending", index=True)

    # 熟化期强制锁定字段
    curing_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    curing_duration_hours: Mapped[int] = mapped_column(Integer, default=48)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # 关联
    product: Mapped["Product"] = relationship("Product", back_populates="orders")