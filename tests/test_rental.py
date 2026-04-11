"""
tests/test_rental.py

Critical business logic tests for the rental engine.
Run with:  uv run pytest tests/test_rental.py -v

All tests use an isolated in-memory SQLite database — no live DB required.
"""

import pytest


pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Test 1 — Cannot rent an item that is under repair
# ---------------------------------------------------------------------------

async def test_cannot_rent_repair_item(client, user_token, repair_item):
    """
    A device with status=repair must be blocked from renting.
    Expected: 409 Conflict
    """
    response = await client.post(
        f"/hardware/{repair_item.id}/rent",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 409
    assert "repair" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 2 — Cannot rent an item that is already in use
# ---------------------------------------------------------------------------

async def test_cannot_rent_in_use_item(client, user_token, in_use_item):
    """
    A device already rented out must not be rentable again.
    Expected: 409 Conflict
    """
    response = await client.post(
        f"/hardware/{in_use_item.id}/rent",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 409
    assert "already" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 3 — Cannot return an item that is not rented out
# ---------------------------------------------------------------------------

async def test_cannot_return_available_item(client, user_token, available_item):
    """
    Returning a device that is still available makes no sense.
    Expected: 409 Conflict
    """
    response = await client.post(
        f"/hardware/{available_item.id}/return",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 409
    assert "not currently rented" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Test 4 — Regular user cannot create another user (admin only)
# ---------------------------------------------------------------------------

async def test_regular_user_cannot_create_user(client, user_token):
    """
    Only admins can create new accounts.
    Expected: 403 Forbidden
    """
    response = await client.post(
        "/users",
        json={
            "email": "hacker@test.com",
            "username": "hacker",
            "password": "password123",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Test 5 — Happy path: can rent an available item
# ---------------------------------------------------------------------------

async def test_can_rent_available_item(client, user_token, available_item):
    """
    Renting an available item should succeed and set status to in_use.
    Expected: 200 OK, status = in_use
    """
    response = await client.post(
        f"/hardware/{available_item.id}/rent",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_use"


# ---------------------------------------------------------------------------
# Test 6 — Happy path: can return an item you rented
# ---------------------------------------------------------------------------

async def test_can_return_rented_item(client, user_token, in_use_item):
    """
    The user who rented an item should be able to return it.
    Expected: 200 OK, status = available
    """
    response = await client.post(
        f"/hardware/{in_use_item.id}/return",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "available"


# ---------------------------------------------------------------------------
# Test 7 — Cannot delete an item that is currently rented out
# ---------------------------------------------------------------------------

async def test_admin_cannot_delete_in_use_item(client, admin_token, in_use_item):
    """
    Admins should not be able to delete hardware that is currently rented.
    Expected: 409 Conflict
    """
    response = await client.delete(
        f"/hardware/{in_use_item.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409