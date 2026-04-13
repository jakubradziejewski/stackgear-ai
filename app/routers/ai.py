"""
app/routers/ai.py

AI-powered features:
  GET  /ai/audit   — Inventory auditor (admin only)
"""

import json
from datetime import date

import google.generativeai as genai
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import require_admin
from app.models.hardware import Hardware
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class AuditFinding(BaseModel):
    item: str
    severity: str        # "info" | "warning" | "error"
    issue: str


class AuditResponse(BaseModel):
    findings: list[AuditFinding]
    summary: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_inventory(items: list[Hardware]) -> str:
    """Convert hardware rows to a clean JSON string for the prompt."""
    today = date.today().isoformat()
    rows = []
    for item in items:
        rows.append({
            "id": item.id,
            "name": item.name,
            "brand": item.brand or "(no brand)",
            "purchase_date": item.purchase_date.isoformat() if item.purchase_date else None,
            "status": item.status.value,
            "rented_by_id": item.rented_by_id,
            "notes": item.notes,
        })
    return json.dumps({"today": today, "inventory": rows}, indent=2)


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
- Only flag genuine issues — do not invent problems.
- Be specific: mention the item name and the exact data that caused the flag.
- If the inventory is clean, return an empty findings list and say so in the summary.
- Return ONLY the raw JSON object — no markdown, no code fences, no explanation.

Inventory data:
{inventory}
"""


# ---------------------------------------------------------------------------
# GET /ai/audit
# ---------------------------------------------------------------------------

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

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip accidental markdown fences if Gemini adds them
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1]
            raw = raw.rsplit("```", 1)[0].strip()

        data = json.loads(raw)
        return AuditResponse(
            findings=[AuditFinding(**f) for f in data.get("findings", [])],
            summary=data.get("summary", ""),
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini returned invalid JSON: {e}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini error: {e}",
        )