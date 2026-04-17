import asyncio
import json
import logging
from datetime import date

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.hardware import Hardware
from app.models.user import User
from app.schemas.hardware import HardwareRead

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash-lite")
GEMINI_TIMEOUT_SECONDS = 12
AI_UNAVAILABLE_MESSAGE = "AI service is temporarily unavailable. Please try again."

class AuditFinding(BaseModel):
    item: str
    severity: str  # "info" | "warning" | "error"
    issue: str


class AuditResponse(BaseModel):
    findings: list[AuditFinding]
    summary: str


class SearchRequest(BaseModel):
    query: str


class SearchResponse(BaseModel):
    items: list[HardwareRead]
    summary: str

def _serialize_inventory(items: list[Hardware]) -> str:
    """Convert hardware rows to a clean JSON string for the audit prompt."""
    today = date.today().isoformat()
    rows = []
    for item in items:
        rows.append(
            {
                "id": item.id,
                "name": item.name,
                "brand": item.brand or "(no brand)",
                "purchase_date": item.purchase_date.isoformat() if item.purchase_date else None,
                "status": item.status.value,
                "rented_by_id": item.rented_by_id,
                "notes": item.notes,
            }
        )
    return json.dumps({"today": today, "inventory": rows}, indent=2)


def _serialize_search_inventory(items: list[Hardware]) -> str:
    """Keep search prompts smaller so Gemini responds like the audit panel does."""
    rows = []
    for item in items:
        rows.append(
            {
                "id": item.id,
                "name": item.name,
                "brand": item.brand,
                "status": item.status.value,
                "notes": item.notes,
            }
        )
    return json.dumps({"inventory": rows}, indent=2)


def _strip_markdown_fences(raw: str) -> str:
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()
    return raw


async def _generate_gemini_json(prompt: str, *, context: str) -> dict:
    """
    Gemini SDK call is blocking; run it off the event loop so one slow AI call
    does not freeze the whole app.
    """
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, prompt),
            timeout=GEMINI_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning("Gemini %s timed out after %ss", context, GEMINI_TIMEOUT_SECONDS)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=AI_UNAVAILABLE_MESSAGE,
        )
    except Exception as exc:
        logger.exception("Gemini %s request failed: %s", context, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=AI_UNAVAILABLE_MESSAGE,
        )

    raw = (getattr(response, "text", "") or "").strip()
    if not raw:
        logger.warning("Gemini %s returned empty text", context)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=AI_UNAVAILABLE_MESSAGE,
        )

    try:
        return json.loads(_strip_markdown_fences(raw))
    except json.JSONDecodeError as exc:
        logger.warning("Gemini %s returned invalid JSON: %s", context, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=AI_UNAVAILABLE_MESSAGE,
        )


AUDIT_PROMPT = """
You are an expert IT asset manager auditing a hardware inventory system.
Today's date is included in the data.

Analyse the inventory below and return a JSON object with this exact structure:
{{
  "findings": [
    {{
      "item": "<item name>",
      "severity": "<info|warning|error>",
      "issue": "<concise description of the problem>"
    }}
  ],
  "summary": "<2-3 sentence overall summary of the inventory health>"
}}

Severity guide:
- error   : urgent problem (unknown status, future purchase date, notes indicate
            danger but item is available, item in_use with no renter assigned)
- warning : should be reviewed (item in repair for a long time, missing brand,
            notes suggest damage, suspicious data)
- info    : minor observation (missing purchase date, cosmetic notes)

Rules:
- Only flag genuine issues - do not invent problems.
- Be specific: mention the item name and the exact data that caused the flag.
- If the inventory is clean, return an empty findings list and say so in the summary.
- Return ONLY the raw JSON object - no markdown, no code fences, no explanation.

Inventory data:
{inventory}
"""


SEARCH_PROMPT = """
You help employees find the most relevant hardware in an internal inventory.

Return a JSON object with this exact structure:
{{
  "item_ids": ["<hardware id>", "<hardware id>"],
  "summary": "<one short sentence saying why these items fit the request>"
}}

Rules:
- Return at most 5 item IDs.
- Use ONLY IDs that appear in the inventory JSON below.
- Prefer available items when possible.
- Match based on name, brand, and notes.
- If nothing fits, return an empty item_ids list.
- Return ONLY the raw JSON object - no markdown, no code fences, no explanation.

User request:
{query}

Inventory data:
{inventory}
"""

@router.get("/audit", response_model=AuditResponse)
async def audit_inventory(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AuditResponse:
    result = await db.execute(select(Hardware).order_by(Hardware.name))
    items = list(result.scalars())

    if not items:
        return AuditResponse(findings=[], summary="No hardware in the inventory.")

    inventory_json = _serialize_inventory(items)
    prompt = AUDIT_PROMPT.format(inventory=inventory_json)

    data = await _generate_gemini_json(prompt, context="audit")
    return AuditResponse(
        findings=[AuditFinding(**finding) for finding in data.get("findings", [])],
        summary=data.get("summary", ""),
    )

@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SearchResponse:
    query = payload.query.strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty.",
        )

    result = await db.execute(select(Hardware).order_by(Hardware.name))
    items = list(result.scalars())

    if not items:
        return SearchResponse(items=[], summary="No hardware in the inventory.")

    inventory_json = _serialize_search_inventory(items)
    prompt = SEARCH_PROMPT.format(query=query, inventory=inventory_json)

    data = await _generate_gemini_json(prompt, context="search")

    items_by_id = {item.id: item for item in items}
    matched_items: list[HardwareRead] = []
    seen: set[str] = set()

    for item_id in data.get("item_ids", []):
        if item_id in seen or item_id not in items_by_id:
            continue
        seen.add(item_id)
        matched_items.append(HardwareRead.model_validate(items_by_id[item_id]))

    return SearchResponse(
        items=matched_items,
        summary=data.get("summary", ""),
    )
