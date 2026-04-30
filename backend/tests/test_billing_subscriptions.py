from contextlib import contextmanager
from unittest.mock import AsyncMock

import pytest


class TestBillingSubscriptionEndpoints:
    def test_subscription_checkout_accepts_frontend_payload(self, client, monkeypatch):
        from app.routers import billing

        mock = AsyncMock(
            return_value={
                "checkout_url": "https://checkout.example.com/session_1",
                "session_id": "session_1",
                "tier": "premium",
                "billing_period": "month",
            }
        )
        monkeypatch.setattr(billing.billing_svc, "create_subscription_checkout", mock)

        response = client.post(
            "/api/billing/subscriptions/checkout",
            json={"tier": "premium", "billing_period": "month"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["checkout_url"].startswith("https://")
        assert data["session_id"] == "session_1"
        mock.assert_awaited_once()

    def test_subscription_checkout_rejects_invalid_tier(self, client):
        response = client.post(
            "/api/billing/subscriptions/checkout",
            json={"tier": "free", "billing_period": "month"},
        )
        assert response.status_code == 400

    def test_subscription_portal_passes_return_url(self, client, monkeypatch):
        from app.routers import billing

        mock = AsyncMock(return_value="https://billing.example.com/portal")
        monkeypatch.setattr(billing.billing_svc, "get_subscription_portal_url", mock)

        response = client.post(
            "/api/billing/subscriptions/portal",
            json={"return_url": "https://app.example.com/billing"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["portal_url"] == "https://billing.example.com/portal"
        mock.assert_awaited_once()

    def test_current_subscription_shape(self, client, monkeypatch):
        from app.routers import billing

        mock = AsyncMock(
            return_value={
                "subscription": None,
                "tier": "free",
                "is_active": False,
            }
        )
        monkeypatch.setattr(billing.billing_svc, "get_current_subscription", mock)

        response = client.get("/api/billing/subscriptions/current")
        assert response.status_code == 200
        data = response.json()
        assert "subscription" in data
        assert "tier" in data
        assert "is_active" in data

    def test_cancel_subscription_returns_cancel_at(self, client, monkeypatch):
        from app.routers import billing

        mock = AsyncMock(
            return_value={"status": "scheduled", "cancel_at": "2026-05-25T00:00:00"}
        )
        monkeypatch.setattr(billing.billing_svc, "cancel_subscription", mock)

        response = client.post("/api/billing/subscriptions/cancel")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["cancel_at"] == "2026-05-25T00:00:00"

    def test_reactivate_subscription_success(self, client, monkeypatch):
        from app.routers import billing

        mock = AsyncMock(return_value={"status": "reactivated"})
        monkeypatch.setattr(billing.billing_svc, "reactivate_subscription", mock)

        response = client.post("/api/billing/subscriptions/reactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "reactivated" in data["message"].lower()

    def test_credit_pack_checkout_accepts_pack_id(self, client, monkeypatch):
        from app.routers import billing

        mock = AsyncMock(
            return_value={
                "checkout_url": "https://checkout.example.com/pack_1",
                "session_id": "pack_1",
                "pack_id": "starter_pack",
            }
        )
        monkeypatch.setattr(billing.billing_svc, "create_credit_pack_checkout", mock)

        response = client.post("/api/billing/credit-packs/checkout", json={"pack_id": "starter_pack"})
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "pack_1"
        mock.assert_awaited_once()

    def test_billing_history_returns_payment_history_response_shape(self, client, monkeypatch):
        from app.routers import billing

        mock = AsyncMock(
            return_value={
                "payments": [],
                "total": 0,
                "limit": 20,
                "offset": 0,
            }
        )
        monkeypatch.setattr(billing.billing_svc, "get_billing_history", mock)

        response = client.get("/api/billing/history?limit=20&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "payments" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_telegram_stars_subscription_order_normalizes_product_metadata(self, client, monkeypatch):
        from app.routers import billing

        mock_create = AsyncMock(
            return_value={
                "order_id": "stars_sub_1",
                "amount": 1299,
                "credits": 100,
                "product_type": "subscription",
                "tier": "premium",
                "billing_period": "1m",
                "status": "pending",
            }
        )
        monkeypatch.setattr(billing.billing_svc, "create_telegram_stars_order", mock_create)

        response = client.post(
            "/api/billing/telegram-stars/orders",
            json={
                "amount_stars": 1299,
                "product_type": "subscription",
                "tier": "premium",
                "billing_period": "month",
                "credits": 100,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["product_type"] == "subscription"
        call = mock_create.await_args.kwargs
        assert call["product_type"] == "subscription"
        assert call["tier"] == "premium"
        assert call["billing_period"] == "1m"

    def test_telegram_stars_credit_pack_order_uses_pack_total_credits(self, client, monkeypatch):
        from app.routers import billing

        class Pack:
            pack_id = "pack_100"
            credits = 100
            bonus_credits = 10

        mock_create = AsyncMock(
            return_value={
                "order_id": "stars_pack_1",
                "amount": 999,
                "credits": 110,
                "product_type": "credit_pack",
                "status": "pending",
            }
        )
        monkeypatch.setattr(billing.pricing_service, "get_credit_packs", AsyncMock(return_value=[Pack()]))
        monkeypatch.setattr(billing.billing_svc, "create_telegram_stars_order", mock_create)

        response = client.post(
            "/api/billing/telegram-stars/orders",
            json={
                "amount_stars": 999,
                "product_type": "credit_pack",
                "pack_id": "pack_100",
            },
        )

        assert response.status_code == 200
        call = mock_create.await_args.kwargs
        assert call["credits"] == 110
        assert call["product_type"] == "credit_pack"

    def test_crypto_credit_pack_order_uses_gateway_service(self, client, monkeypatch):
        from app.routers import billing

        mock_create = AsyncMock(
            return_value={
                "order_id": "crypto_pack_1",
                "asset": "USDT",
                "network": "POLYGON",
                "amount_crypto": 9.99,
                "credits": 110,
                "product_type": "credit_pack",
                "status": "pending",
                "payment_address": "TWallet",
                "raw": {},
            }
        )
        monkeypatch.setattr(billing.billing_svc, "create_crypto_order", mock_create)

        response = client.post(
            "/api/billing/crypto/orders",
            json={
                "asset": "USDT",
                "network": "POLYGON",
                "product_type": "credit_pack",
                "pack_id": "pack_100",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == "crypto_pack_1"
        call = mock_create.await_args.kwargs
        assert call["asset"] == "USDT"
        assert call["network"] == "POLYGON"
        assert call["product_type"] == "credit_pack"
        assert call["pack_id"] == "pack_100"

    def test_crypto_subscription_order_is_one_time_entitlement(self, client, monkeypatch):
        from app.routers import billing

        mock_create = AsyncMock(
            return_value={
                "order_id": "crypto_sub_1",
                "asset": "USDC",
                "network": "POLYGON",
                "amount_crypto": 13.99,
                "credits": 100,
                "product_type": "subscription",
                "tier": "premium",
                "billing_period": "1m",
                "status": "pending",
                "raw": {},
            }
        )
        monkeypatch.setattr(billing.billing_svc, "create_crypto_order", mock_create)

        response = client.post(
            "/api/billing/crypto/orders",
            json={
                "asset": "USDC",
                "network": "POLYGON",
                "product_type": "subscription",
                "tier": "premium",
                "billing_period": "1m",
            },
        )

        assert response.status_code == 200
        call = mock_create.await_args.kwargs
        assert call["product_type"] == "subscription"
        assert call["tier"] == "premium"
        assert call["billing_period"] == "1m"

    def test_crypto_order_rejects_unsupported_asset_network_pair(self, client, monkeypatch):
        from app.routers import billing

        response = client.post(
            "/api/billing/crypto/orders",
            json={
                "asset": "USDC",
                "network": "TRC20",
                "product_type": "credit_pack",
                "pack_id": "pack_100",
            },
        )

        assert response.status_code == 422
        assert "network must be POLYGON" in response.text

    @pytest.mark.asyncio
    async def test_local_crypto_order_uses_configured_address_pool(self, monkeypatch):
        from app.services import billing_service as billing_module
        from app.services.billing_service import BillingService

        async def config_value(key, default=None):
            values = {
                "CRYPTO_PAYMENT_GATEWAY_ENABLED": "false",
                "USDT_PAYMENT_GATEWAY_ENABLED": "false",
                "CRYPTO_PAYMENT_ADDRESS_POOL_USDT_POLYGON": "0xWalletA, 0xWalletB",
            }
            return values.get(key, default)

        monkeypatch.setattr(billing_module, "get_config_value", config_value)

        order = await BillingService()._create_crypto_gateway_order(
            order_id="00000000-0000-0000-0000-000000000001",
            user_id="user_001",
            asset="USDT",
            network="POLYGON",
            amount_usd_cents=999,
            credits=100,
            product_type="credit_pack",
            pack_id="pack_100",
            tier=None,
            billing_period=None,
            metadata={},
        )

        assert order["gateway"] == "local"
        assert order["payment_address"] == "0xWalletB"
        assert order["payment_uri"].startswith("ethereum:0xWalletB?")
        assert "amount=9.99" in order["payment_uri"]

    @pytest.mark.asyncio
    async def test_paid_subscription_order_repairs_missing_credit_grant(self, monkeypatch):
        from app.models.credit_transaction import CreditTransaction
        from app.models.user import User
        from app.services.billing_service import BillingService
        from app.services.credit_service import credit_service

        stored_order = {
            "order_id": "stars_sub_repair",
            "status": "paid",
            "user_id": "test_user_001",
            "credits": 100,
            "product_type": "subscription",
            "tier": "premium",
            "billing_period": "1m",
            "credits_applied": False,
            "subscription_applied": False,
        }
        user = User(id="test_user_001", email="test@example.com")

        class Query:
            def __init__(self, result):
                self.result = result

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self.result

        class Session:
            def query(self, model):
                if model is CreditTransaction:
                    return Query(None)
                if model is User:
                    return Query(user)
                return Query(None)

        class Db:
            @contextmanager
            def transaction(self):
                yield Session()

        class Redis:
            def __init__(self):
                self.saved_order = None
                self.deleted_keys = []

            async def get_json(self, key):
                return dict(stored_order)

            async def set_json(self, key, value, ex=None):
                self.saved_order = value
                return True

            async def delete(self, key):
                self.deleted_keys.append(key)
                return True

        redis = Redis()
        add_credits = AsyncMock(return_value=True)
        monkeypatch.setattr(credit_service, "add_credits", add_credits)

        result = await BillingService(redis=redis, db=Db()).mark_telegram_stars_order_paid(
            order_id="stars_sub_repair",
            charge_id="charge_001",
            webhook_payload={"status": "paid"},
        )

        assert result["status"] == "paid"
        assert result["already_processed"] is True
        assert result["credits_applied"] is True
        assert result["subscription_applied"] is True
        add_credits.assert_awaited_once()
        assert add_credits.await_args.kwargs["amount"] == 100
        assert add_credits.await_args.kwargs["transaction_type"] == "subscription"
        assert redis.saved_order["credits_applied"] is True
        assert "user:balance:test_user_001" in redis.deleted_keys
