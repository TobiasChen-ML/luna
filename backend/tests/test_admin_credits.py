import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient


class TestAdminCreditsConfig:
    @pytest.fixture(autouse=True)
    def bypass_rate_limit(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_get_credit_config(self, admin_client: TestClient):
        response = admin_client.get("/api/admin/credits/config")
        assert response.status_code == 200
        data = response.json()
        assert "message_cost" in data
        assert "voice_cost" in data
        assert "image_cost" in data
        assert "video_cost" in data

    def test_update_credit_config(self, admin_client: TestClient):
        response = admin_client.put("/api/admin/credits/config", json={
            "message_cost": 0.15,
            "image_cost": 3
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_update_credit_config_empty_data(self, admin_client: TestClient):
        response = admin_client.put("/api/admin/credits/config", json={})
        assert response.status_code == 400


class TestAdminAdjustCredits:
    @pytest.fixture(autouse=True)
    def bypass_rate_limit(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_adjust_add_credits(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.credit_service.admin_adjust_credits", new_callable=AsyncMock) as mock_adjust:
            mock_adjust.return_value = True
            
            response = admin_client.post("/api/admin/credits/adjust", json={
                "user_id": "test_user_001",
                "amount": 50.0,
                "description": "Compensation for bug"
            })
            
            assert response.status_code == 200
            assert response.json()["success"] is True
            mock_adjust.assert_called_once()

    def test_adjust_deduct_credits(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.credit_service.admin_adjust_credits", new_callable=AsyncMock) as mock_adjust:
            mock_adjust.return_value = True
            
            response = admin_client.post("/api/admin/credits/adjust", json={
                "user_id": "test_user_001",
                "amount": -20.0,
                "description": "Penalty for abuse"
            })
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_adjust_user_not_found(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.credit_service.admin_adjust_credits", new_callable=AsyncMock) as mock_adjust:
            from app.services.credit_service import InsufficientCreditsError
            mock_adjust.side_effect = ValueError("User nonexistent not found")
            
            response = admin_client.post("/api/admin/credits/adjust", json={
                "user_id": "nonexistent_user",
                "amount": 50.0,
                "description": "Test"
            })
            
            assert response.status_code == 404

    def test_adjust_insufficient_credits(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.credit_service.admin_adjust_credits", new_callable=AsyncMock) as mock_adjust:
            from app.services.credit_service import InsufficientCreditsError
            mock_adjust.side_effect = InsufficientCreditsError("Insufficient credits")
            
            response = admin_client.post("/api/admin/credits/adjust", json={
                "user_id": "test_user_001",
                "amount": -1000.0,
                "description": "Too much deduction"
            })
            
            assert response.status_code == 400

    def test_adjust_requires_admin(self, client: TestClient):
        response = client.post("/api/admin/credits/adjust", json={
            "user_id": "test_user_001",
            "amount": 50.0,
            "description": "Test"
        })
        assert response.status_code in (401, 403, 404)


class TestAdminCreditPacks:
    @pytest.fixture(autouse=True)
    def bypass_rate_limit(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_get_credit_packs(self, admin_client: TestClient):
        response = admin_client.get("/api/admin/credits/packs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_credit_pack(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.pricing_service.create_credit_pack", new_callable=AsyncMock) as mock_create:
            mock_pack = MagicMock()
            mock_pack.to_dict = lambda: {"pack_id": "test_pack", "name": "Test Pack", "credits": 100}
            mock_create.return_value = mock_pack
            
            response = admin_client.post("/api/admin/credits/packs", json={
                "pack_id": "test_pack",
                "name": "Test Pack",
                "credits": 100,
                "price_cents": 499
            })
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_update_credit_pack(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.pricing_service.update_credit_pack", new_callable=AsyncMock) as mock_update:
            mock_pack = MagicMock()
            mock_pack.to_dict = lambda: {"pack_id": "small", "name": "Updated Small Pack"}
            mock_update.return_value = mock_pack
            
            response = admin_client.put("/api/admin/credits/packs/small", json={
                "name": "Updated Small Pack"
            })
            
            assert response.status_code == 200

    def test_delete_credit_pack(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.pricing_service.delete_credit_pack", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            
            response = admin_client.delete("/api/admin/credits/packs/test_pack")
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_delete_nonexistent_pack(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.pricing_service.delete_credit_pack", new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            
            response = admin_client.delete("/api/admin/credits/packs/nonexistent")
            
            assert response.status_code == 404


class TestAdminTransactions:
    @pytest.fixture(autouse=True)
    def bypass_rate_limit(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_list_transactions(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.credit_service.get_all_transactions", new_callable=AsyncMock) as mock_get:
            mock_tx = MagicMock()
            mock_tx.to_dict = lambda: {"id": "tx_001", "amount": 100}
            mock_get.return_value = ([mock_tx], 1)
            
            response = admin_client.get("/api/admin/credits/transactions")
            
            assert response.status_code == 200
            data = response.json()
            assert "transactions" in data
            assert "total" in data

    def test_list_transactions_with_filters(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.credit_service.get_all_transactions", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = ([], 0)
            
            response = admin_client.get("/api/admin/credits/transactions?user_id=test_user&transaction_type=purchase")
            
            assert response.status_code == 200
            call_args = mock_get.call_args
            assert call_args.kwargs["user_id"] == "test_user"
            assert call_args.kwargs["transaction_type"] == "purchase"


class TestAdminSubscriptionPlans:
    @pytest.fixture(autouse=True)
    def bypass_rate_limit(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_get_subscription_plans(self, admin_client: TestClient):
        response = admin_client.get("/api/admin/credits/plans")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_update_subscription_plan(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.pricing_service.update_subscription_plan", new_callable=AsyncMock) as mock_update:
            mock_plan = MagicMock()
            mock_plan.to_dict = lambda: {"period": "1m", "price_cents": 999}
            mock_update.return_value = mock_plan
            
            response = admin_client.put("/api/admin/credits/plans/1m", json={
                "price_cents": 999
            })
            
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_update_nonexistent_plan(self, admin_client: TestClient):
        with patch("app.routers.admin.credits.pricing_service.update_subscription_plan", new_callable=AsyncMock) as mock_update:
            mock_update.side_effect = ValueError("Plan not found")
            
            response = admin_client.put("/api/admin/credits/plans/99y", json={
                "price_cents": 99900
            })
            
            assert response.status_code == 404
