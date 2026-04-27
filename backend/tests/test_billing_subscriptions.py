from unittest.mock import AsyncMock


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
