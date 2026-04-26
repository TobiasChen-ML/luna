from datetime import datetime
from types import SimpleNamespace

import pytest

from app.routers import auth


@pytest.mark.asyncio
async def test_auth_me_returns_database_credit_balance(monkeypatch):
    async def fake_get_user_by_id(user_id: str):
        assert user_id == "usr_real_balance"
        return SimpleNamespace(
            id=user_id,
            email="real@example.com",
            display_name="Real User",
            avatar_url="https://example.com/avatar.png",
            created_at=datetime(2026, 1, 1),
            updated_at=datetime(2026, 1, 2),
        )

    async def fake_get_balance(user_id: str):
        assert user_id == "usr_real_balance"
        return {
            "total": 7.8,
            "subscription_tier": "free",
        }

    monkeypatch.setattr(auth.db_svc, "get_user_by_id", fake_get_user_by_id)
    monkeypatch.setattr(auth.credit_service, "get_balance", fake_get_balance)

    response = await auth.get_current_user(
        request=SimpleNamespace(),
        user=SimpleNamespace(
            id="usr_real_balance",
            email="placeholder@example.com",
            display_name="Placeholder",
            avatar_url=None,
            subscription_tier="premium",
            credits=1000,
            is_admin=True,
        ),
    )

    assert response.email == "real@example.com"
    assert response.display_name == "Real User"
    assert response.credits == 7.8
    assert response.subscription_tier == "free"
    assert response.is_admin is True
