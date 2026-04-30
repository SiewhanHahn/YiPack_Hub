# app/cms/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class ContentBase(BaseModel):
    content_type: str = Field(..., description="内容类型：certificate, profile, product等")
    title: str = Field(..., max_length=100)
    image_url: Optional[str] = None
    content_text: Optional[str] = None
    is_active: bool = True


class ContentCreate(ContentBase):
    pass


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    image_url: Optional[str] = None
    content_text: Optional[str] = None
    is_active: Optional[bool] = None


class ContentResponse(ContentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)