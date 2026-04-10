import json
import uuid
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.hardware import Hardware
from app.models.enums import HardwareStatus
from app.schemas.hardware import HardwareCreate


DATA_FILE = Path(__file__).parent.parent.parent / "data" / "seed_hardware.json"


def load_json() -> list[dict]:
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def map_status(raw: str) -> HardwareStatus:
    mapping = {
        "available": HardwareStatus.AVAILABLE,
        "in use":    HardwareStatus.IN_USE,
        "repair":    HardwareStatus.REPAIR,
    }
    return mapping.get(raw.lower().strip(), HardwareStatus.UNKNOWN)


async def seed_hardware(session: AsyncSession) -> None:
    items = load_json()
    seen_ids = set()

    for item in items:
        if item["id"] in seen_ids:
            item = {**item, "id": str(uuid.uuid4())}
        seen_ids.add(item["id"])

        try:
            validated = HardwareCreate(
                name=item["name"],
                brand=item.get("brand") or None,
                purchase_date=item.get("purchaseDate"),
                notes=item.get("notes"),
            )
        except Exception as e:
            print(f"  ✗ Skipping '{item.get('name', 'unknown')}': {e}")
            continue

        session.add(Hardware(
            id=str(uuid.uuid4()),
            name=validated.name,
            brand=validated.brand,
            purchase_date=validated.purchase_date,
            status=map_status(item.get("status", "")),
            rented_by_id=None,
            notes=validated.notes,
        ))
        print(f"  + {item['name']}")