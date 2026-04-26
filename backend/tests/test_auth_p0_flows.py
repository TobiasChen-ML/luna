from types import SimpleNamespace
from unittest.mock import AsyncMock


class TestAuthP0Flows:
    def test_register_initiate_returns_email(self, client, monkeypatch):
        from app.routers import auth

        monkeypatch.setattr(auth.redis_svc, "set_json", AsyncMock(return_value=True))

        resp = client.post(
            "/api/auth/register/initiate",
            json={
                "email": "newuser@example.com",
                "password": "StrongPwd123",
                "age_consent_given": True,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["email"] == "newuser@example.com"

    def test_verify_email_token_path(self, client, monkeypatch):
        from app.routers import auth

        monkeypatch.setattr(
            auth.redis_svc,
            "get_json",
            AsyncMock(return_value={"email": "verified@example.com"}),
        )
        monkeypatch.setattr(auth.redis_svc, "set_json", AsyncMock(return_value=True))
        monkeypatch.setattr(auth.redis_svc, "delete", AsyncMock(return_value=True))
        monkeypatch.setattr(auth, "_get_user_by_email", AsyncMock(return_value=None))
        monkeypatch.setattr(
            auth,
            "FirebaseService",
            lambda: SimpleNamespace(_initialized=False, create_custom_token=lambda *_: None),
        )

        resp = client.post("/api/auth/verify-email", json={"token": "token_abc"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["user"]["email"] == "verified@example.com"

    def test_register_upsert_new_user(self, client, monkeypatch):
        from app.routers import auth

        fake_user = SimpleNamespace(
            id="firebase_123",
            email="new@example.com",
            display_name="New User",
            tier="free",
            credits=10.0,
            created_at=None,
            updated_at=None,
        )
        monkeypatch.setattr(auth, "_get_user_by_email", AsyncMock(return_value=None))
        monkeypatch.setattr(auth.db_svc, "create_user", AsyncMock(return_value=fake_user))
        monkeypatch.setattr(auth.credit_service, "grant_signup_bonus", AsyncMock(return_value=True))

        resp = client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "firebase_uid": "firebase_123", "is_adult": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_new_user"] is True
        assert data["user"]["id"] == "firebase_123"

    def test_register_existing_user_is_idempotent(self, client, monkeypatch):
        from app.routers import auth

        existing = SimpleNamespace(
            id="existing_1",
            email="existing@example.com",
            display_name="Existing",
            tier="free",
            credits=20.0,
            created_at=None,
            updated_at=None,
        )
        monkeypatch.setattr(auth, "_get_user_by_email", AsyncMock(return_value=existing))
        monkeypatch.setattr(auth.db_svc, "create_user", AsyncMock())
        monkeypatch.setattr(auth.credit_service, "grant_signup_bonus", AsyncMock())

        resp = client.post(
            "/api/auth/register",
            json={"email": "existing@example.com", "firebase_uid": "existing_1"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["is_new_user"] is False
        auth.db_svc.create_user.assert_not_awaited()

    def test_login_returns_401_when_user_missing(self, client, monkeypatch):
        from app.routers import auth

        monkeypatch.setattr(auth, "_get_user_by_email", AsyncMock(return_value=None))
        resp = client.post(
            "/api/auth/login",
            json={"email": "missing@example.com", "password": "Password1"},
        )
        assert resp.status_code == 401

    def test_daily_checkin_grants_credits(self, client, monkeypatch):
        from app.routers import auth

        monkeypatch.setattr(auth.redis_svc, "exists", AsyncMock(return_value=False))
        monkeypatch.setattr(auth.redis_svc, "set", AsyncMock(return_value=True))
        monkeypatch.setattr(auth.redis_svc, "delete", AsyncMock(return_value=True))
        monkeypatch.setattr(auth.credit_service, "add_credits", AsyncMock(return_value=True))
        monkeypatch.setattr(auth.credit_service, "get_balance", AsyncMock(return_value={"total": 123.0}))

        resp = client.post("/api/auth/checkin")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["credits_granted"] == 2
        assert data["new_balance"] == 123.0

    def test_daily_checkin_second_time_returns_429(self, client, monkeypatch):
        from app.routers import auth

        monkeypatch.setattr(auth.redis_svc, "exists", AsyncMock(return_value=True))
        resp = client.post("/api/auth/checkin")
        assert resp.status_code == 429

    def test_daily_checkin_succeeds_when_redis_unavailable(self, client, monkeypatch):
        from app.routers import auth

        monkeypatch.setattr(auth.redis_svc, "exists", AsyncMock(side_effect=RuntimeError("redis down")))
        monkeypatch.setattr(auth.redis_svc, "set", AsyncMock())
        monkeypatch.setattr(auth.redis_svc, "delete", AsyncMock())
        monkeypatch.setattr(auth.credit_service, "add_credits", AsyncMock(return_value=True))
        monkeypatch.setattr(auth.credit_service, "get_balance", AsyncMock(return_value={"total": 125.0}))

        resp = client.post("/api/auth/checkin")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["new_balance"] == 125.0
