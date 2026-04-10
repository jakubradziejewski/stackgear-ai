from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional
from app.models.enums import HardwareStatus


class HardwareCreate(BaseModel):
    """What admin sends when adding new hardware."""
    name: str
    brand: Optional[str] = None
    purchase_date: Optional[date] = None
    notes: Optional[str] = None


class HardwareRead(BaseModel):
    """What the API returns when reading hardware."""
    id: str
    name: str
    brand: Optional[str] = None
    purchase_date: Optional[date] = None
    status: HardwareStatus
    rented_by_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class HardwareUpdate(BaseModel):
    """What admin sends when updating hardware — all fields optional."""
    name: Optional[str] = None
    brand: Optional[str] = None
    purchase_date: Optional[date] = None
    notes: Optional[str] = None


class HardwareStatusUpdate(BaseModel):
    """Specifically for toggling repair status."""
    status: HardwareStatus