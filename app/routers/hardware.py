import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.hardware import Hardware
from app.models.enums import HardwareStatus
from app.models.user import User
from app.schemas.hardware import HardwareCreate, HardwareRead, HardwareUpdate
from app.sockets import sio

router = APIRouter(prefix="/hardware", tags=["hardware"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_or_404(hardware_id: str, db: AsyncSession) -> Hardware:
    result = await db.execute(select(Hardware).where(Hardware.id == hardware_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hardware not found")
    return item


async def _broadcast():
    """Notify all connected clients that hardware state has changed."""
    await sio.emit("hardware_updated")


# ---------------------------------------------------------------------------
# List  —  GET /hardware
# ---------------------------------------------------------------------------

@router.get("", response_model=list[HardwareRead])
async def list_hardware(
    status_filter: HardwareStatus | None = Query(None, alias="status"),
    sort_by: str = Query("name", pattern="^(name|purchase_date|status)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[HardwareRead]:
    stmt = select(Hardware)
    if status_filter is not None:
        stmt = stmt.where(Hardware.status == status_filter)
    col = getattr(Hardware, sort_by)
    stmt = stmt.order_by(col.desc() if order == "desc" else col.asc())
    result = await db.execute(stmt)
    return [HardwareRead.model_validate(row) for row in result.scalars()]


# ---------------------------------------------------------------------------
# Create  —  POST /hardware   (admin only)
# ---------------------------------------------------------------------------

@router.post("", response_model=HardwareRead, status_code=status.HTTP_201_CREATED)
async def create_hardware(
    payload: HardwareCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> HardwareRead:
    item = Hardware(
        id=str(uuid.uuid4()),
        name=payload.name,
        brand=payload.brand,
        purchase_date=payload.purchase_date,
        notes=payload.notes,
        status=HardwareStatus.AVAILABLE,
    )
    db.add(item)
    await db.flush()
    await _broadcast()
    return HardwareRead.model_validate(item)


# ---------------------------------------------------------------------------
# Get one  —  GET /hardware/{id}
# ---------------------------------------------------------------------------

@router.get("/{hardware_id}", response_model=HardwareRead)
async def get_hardware(
    hardware_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> HardwareRead:
    item = await _get_or_404(hardware_id, db)
    return HardwareRead.model_validate(item)


# ---------------------------------------------------------------------------
# Update metadata  —  PATCH /hardware/{id}   (admin only)
# ---------------------------------------------------------------------------

@router.patch("/{hardware_id}", response_model=HardwareRead)
async def update_hardware(
    hardware_id: str,
    payload: HardwareUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> HardwareRead:
    item = await _get_or_404(hardware_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    await _broadcast()
    return HardwareRead.model_validate(item)


# ---------------------------------------------------------------------------
# Toggle repair  —  PATCH /hardware/{id}/repair   (admin only)
# ---------------------------------------------------------------------------

@router.patch("/{hardware_id}/repair", response_model=HardwareRead)
async def toggle_repair(
    hardware_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> HardwareRead:
    item = await _get_or_404(hardware_id, db)
    if item.status == HardwareStatus.IN_USE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot toggle repair status while item is in use — return it first.",
        )
    item.status = (
        HardwareStatus.REPAIR
        if item.status == HardwareStatus.AVAILABLE
        else HardwareStatus.AVAILABLE
    )
    await db.flush()
    await _broadcast()
    return HardwareRead.model_validate(item)


# ---------------------------------------------------------------------------
# Delete  —  DELETE /hardware/{id}   (admin only)
# ---------------------------------------------------------------------------

@router.delete("/{hardware_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hardware(
    hardware_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> None:
    item = await _get_or_404(hardware_id, db)
    if item.status == HardwareStatus.IN_USE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete an item that is currently rented out.",
        )
    await db.delete(item)
    await _broadcast()


# ---------------------------------------------------------------------------
# Rent  —  POST /hardware/{id}/rent
# ---------------------------------------------------------------------------

@router.post("/{hardware_id}/rent", response_model=HardwareRead)
async def rent_hardware(
    hardware_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HardwareRead:
    item = await _get_or_404(hardware_id, db)
    if item.status == HardwareStatus.IN_USE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item is already rented out.")
    if item.status == HardwareStatus.REPAIR:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item is under repair and cannot be rented.")
    if item.status == HardwareStatus.UNKNOWN:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item has an unknown status and cannot be rented.")
    item.status = HardwareStatus.IN_USE
    item.rented_by_id = current_user.id
    await db.flush()
    await _broadcast()
    return HardwareRead.model_validate(item)


# ---------------------------------------------------------------------------
# Return  —  POST /hardware/{id}/return
# ---------------------------------------------------------------------------

@router.post("/{hardware_id}/return", response_model=HardwareRead)
async def return_hardware(
    hardware_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HardwareRead:
    item = await _get_or_404(hardware_id, db)
    if item.status != HardwareStatus.IN_USE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Item is not currently rented out.")
    if not current_user.is_admin and item.rented_by_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only return items you have rented.")
    item.status = HardwareStatus.AVAILABLE
    item.rented_by_id = None
    await db.flush()
    await _broadcast()
    return HardwareRead.model_validate(item)