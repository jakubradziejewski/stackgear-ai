from pydantic import BaseModel, field_validator
from datetime import date, datetime
from typing import Optional
from app.models.enums import HardwareStatus


class HardwareCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    purchase_date: Optional[str | date] = None
    notes: Optional[str] = None

    @field_validator("purchase_date", mode="before")
    @classmethod
    def parse_purchase_date(cls, v):
        if v is None or isinstance(v, date):
            return v
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(v, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: {v!r} — expected YYYY-MM-DD or DD-MM-YYYY")


class HardwareRead(BaseModel):
    id: str
    name: str
    brand: Optional[str] = None
    purchase_date: Optional[date] = None
    status: HardwareStatus
    rented_by_id: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class HardwareUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    purchase_date: Optional[str | date] = None
    notes: Optional[str] = None

    @field_validator("purchase_date", mode="before")
    @classmethod
    def parse_purchase_date(cls, v):
        if v is None or isinstance(v, date):
            return v
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                return datetime.strptime(v, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Cannot parse date: {v!r} — expected YYYY-MM-DD or DD-MM-YYYY")


class HardwareStatusUpdate(BaseModel):
    status: HardwareStatus