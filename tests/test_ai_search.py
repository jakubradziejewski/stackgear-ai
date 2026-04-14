import json

import pytest

from app.routers import ai as ai_router


pytestmark = pytest.mark.asyncio


class FakeGeminiResponse:
    def __init__(self, text: str):
        self.text = text


async def test_audit_inventory_still_returns_findings(
    client,
    admin_token,
    available_item,
    monkeypatch,
):
    def fake_generate_content(prompt: str):
        assert available_item.name in prompt
        payload = {
            "findings": [
                {
                    "item": available_item.name,
                    "severity": "info",
                    "issue": "Minor note for test coverage.",
                }
            ],
            "summary": "Audit completed successfully.",
        }
        return FakeGeminiResponse(json.dumps(payload))

    monkeypatch.setattr(ai_router.model, "generate_content", fake_generate_content)

    response = await client.get(
        "/ai/audit",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Audit completed successfully."
    assert data["findings"][0]["item"] == available_item.name


async def test_semantic_search_returns_ranked_items(
    client,
    user_token,
    available_item,
    repair_item,
    monkeypatch,
):
    def fake_generate_content(prompt: str):
        assert "record a presentation" in prompt
        payload = {
            "item_ids": [repair_item.id, available_item.id],
            "summary": "These are the closest matches for recording a presentation.",
        }
        return FakeGeminiResponse(f"```json\n{json.dumps(payload)}\n```")

    monkeypatch.setattr(ai_router.model, "generate_content", fake_generate_content)

    response = await client.post(
        "/ai/search",
        json={"query": "I need something to record a presentation"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data["items"]] == [repair_item.id, available_item.id]
    assert "recording a presentation" in data["summary"].lower()


async def test_semantic_search_rejects_blank_query(client, user_token):
    response = await client.post(
        "/ai/search",
        json={"query": "   "},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Search query cannot be empty."


async def test_semantic_search_ignores_unknown_or_duplicate_ids(
    client,
    user_token,
    available_item,
    monkeypatch,
):
    def fake_generate_content(prompt: str):
        payload = {
            "item_ids": ["missing-item", available_item.id, available_item.id],
            "summary": "One real match was found.",
        }
        return FakeGeminiResponse(json.dumps(payload))

    monkeypatch.setattr(ai_router.model, "generate_content", fake_generate_content)

    response = await client.post(
        "/ai/search",
        json={"query": "Need a laptop"},
        headers={"Authorization": f"Bearer {user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data["items"]] == [available_item.id]
    assert data["summary"] == "One real match was found."
