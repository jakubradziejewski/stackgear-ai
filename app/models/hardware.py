import uuid
from datetime import date, datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, DateTime, Text, Enum as SAEnum, ForeignKey
from app.core.database import Base
from app.models.enums import HardwareStatus

class Hardware(Base):
    __tablename__ = "hardware"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    brand: Mapped[str | None] = mapped_column(String, nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[HardwareStatus] = mapped_column(
        SAEnum(HardwareStatus, name="hardwarestatus"),
        default=HardwareStatus.AVAILABLE,
        nullable=False
    )
    rented_by_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        default=None
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )