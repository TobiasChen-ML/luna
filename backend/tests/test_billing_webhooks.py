import pytest
import json
import hmac
import hashlib
import time
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app


def compute_ccbill_signature(payload: dict, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        json.dumps(payload, separators=(',', ':')).encode(),
        hashlib.sha256
    ).hexdigest()


def compute_usdt_signature(payload: dict, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        json.dumps(payload, separators=(',', ':')).encode(),
        hashlib.sha256
    ).hexdigest()


def compute_telegram_signature(payload: dict, bot_token: str) -> str:
    sorted_items = sorted(payload.items())
    data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted_items)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    return hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()


class TestStripeWebhook:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_stripe_webhook_payment_success(self, client: TestClient, monkeypatch):
        mock_result = {"status": "success", "credits_added": 100}
        
        with patch("app.services.billing_service.BillingService.handle_stripe_webhook", new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = mock_result
            
            payload = json.dumps({"id": "evt_001", "type": "checkout.session.completed"})
            response = client.post(
                "/api/billing/webhooks/stripe",
                content=payload,
                headers={"Stripe-Signature": "test_sig", "Content-Type": "application/json"}
            )
        
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_stripe_webhook_missing_signature(self, client: TestClient):
        response = client.post(
            "/api/billing/webhooks/stripe",
            json={"id": "evt_001"},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 401
        assert "Missing signature" in response.json()["detail"]


class TestCCBillWebhook:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_ccbill_payment_success_adds_credits(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_ccbill_signature", return_value=True):
            with patch("app.routers.billing.credit_service.add_credits", new_callable=AsyncMock) as mock_add:
                mock_add.return_value = True
                
                payload = {
                    "event": "payment_success",
                    "user_id": "test_user_001",
                    "credits": 100,
                    "order_id": "order_001",
                    "timestamp": time.time()
                }
                signature = "test_signature"
                
                response = client.post(
                    "/api/billing/webhooks/ccbill",
                    json=payload,
                    headers={"X-CCBill-Signature": signature}
                )
        
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_ccbill_invalid_signature(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_ccbill_signature", return_value=False):
            payload = {"event": "payment_success", "timestamp": time.time()}
            response = client.post(
                "/api/billing/webhooks/ccbill",
                json=payload,
                headers={"X-CCBill-Signature": "invalid_sig"}
            )
        
        assert response.status_code == 401
        assert "Invalid signature" in response.json()["detail"]

    def test_ccbill_expired_webhook(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_ccbill_signature", return_value=True):
            payload = {
                "event": "payment_success",
                "timestamp": time.time() - 400
            }
            response = client.post(
                "/api/billing/webhooks/ccbill",
                json=payload,
                headers={"X-CCBill-Signature": "valid_sig"}
            )
        
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()

    def test_ccbill_missing_user_id_logs_warning(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_ccbill_signature", return_value=True):
            payload = {
                "event": "payment_success",
                "credits": 100,
                "timestamp": time.time()
            }
            response = client.post(
                "/api/billing/webhooks/ccbill",
                json=payload,
                headers={"X-CCBill-Signature": "valid_sig"}
            )
        
        assert response.status_code == 200


class TestUSDTWebhook:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_usdt_payment_confirmed_adds_credits(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_usdt_signature", return_value=True):
            with patch("app.core.config.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.ccbill_client_secret = "test_secret"
                mock_get_settings.return_value = mock_settings
                
                with patch("app.routers.billing.credit_service.add_credits", new_callable=AsyncMock) as mock_add:
                    mock_add.return_value = True
                    
                    payload = {
                        "status": "confirmed",
                        "user_id": "test_user_001",
                        "credits": 50,
                        "tx_hash": "0xabc123",
                        "timestamp": time.time()
                    }
                    
                    response = client.post(
                        "/api/billing/webhooks/usdt",
                        json=payload,
                        headers={"X-Webhook-Signature": "valid_sig"}
                    )
        
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_usdt_invalid_signature(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_usdt_signature", return_value=False):
            with patch("app.core.config.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.ccbill_client_secret = "test_secret"
                mock_get_settings.return_value = mock_settings
                
                payload = {"status": "confirmed", "timestamp": time.time()}
                response = client.post(
                    "/api/billing/webhooks/usdt",
                    json=payload,
                    headers={"X-Webhook-Signature": "invalid_sig"}
                )
        
        assert response.status_code == 401

    def test_usdt_pending_status_no_credits(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_usdt_signature", return_value=True):
            with patch("app.core.config.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.ccbill_client_secret = "test_secret"
                mock_get_settings.return_value = mock_settings
                
                with patch("app.routers.billing.credit_service.add_credits", new_callable=AsyncMock) as mock_add:
                    payload = {
                        "status": "pending",
                        "user_id": "test_user_001",
                        "credits": 50,
                        "tx_hash": "0xabc123",
                        "timestamp": time.time()
                    }
                    
                    response = client.post(
                        "/api/billing/webhooks/usdt",
                        json=payload,
                        headers={"X-Webhook-Signature": "valid_sig"}
                    )
        
        assert response.status_code == 200
        mock_add.assert_not_called()


class TestTelegramStarsWebhook:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_telegram_stars_payment_success_adds_credits(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_telegram_signature", return_value=True):
            with patch("app.core.config.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.telegram_bot_token = "test_bot_token"
                mock_get_settings.return_value = mock_settings
                
                with patch("app.routers.billing.credit_service.add_credits", new_callable=AsyncMock) as mock_add:
                    mock_add.return_value = True
                    
                    payload = {
                        "status": "paid",
                        "user_id": "test_user_001",
                        "credits": 100,
                        "order_id": "stars_order_001",
                        "auth_date": int(time.time())
                    }
                    
                    response = client.post(
                        "/api/billing/webhooks/telegram-stars",
                        json=payload
                    )
        
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_telegram_stars_invalid_signature(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_telegram_signature", return_value=False):
            with patch("app.core.config.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.telegram_bot_token = "test_bot_token"
                mock_get_settings.return_value = mock_settings
                
                payload = {"status": "paid", "auth_date": int(time.time())}
                response = client.post(
                    "/api/billing/webhooks/telegram-stars",
                    json=payload
                )
        
        assert response.status_code == 401

    def test_telegram_stars_bot_token_not_configured(self, client: TestClient, monkeypatch):
        with patch("app.core.config.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_settings.telegram_bot_token = None
            mock_get_settings.return_value = mock_settings
            
            payload = {"status": "paid", "auth_date": int(time.time())}
            response = client.post(
                "/api/billing/webhooks/telegram-stars",
                json=payload
            )
        
        assert response.status_code == 503


class TestWebhookCreditIntegration:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_ccbill_credits_added_to_correct_user(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_ccbill_signature", return_value=True):
            with patch("app.routers.billing.credit_service.add_credits", new_callable=AsyncMock) as mock_add:
                payload = {
                    "event": "payment_success",
                    "user_id": "specific_user_123",
                    "credits": 250,
                    "order_id": "order_xyz",
                    "timestamp": time.time()
                }
                
                response = client.post(
                    "/api/billing/webhooks/ccbill",
                    json=payload,
                    headers={"X-CCBill-Signature": "sig"}
                )
                
                mock_add.assert_called_once_with(
                    user_id="specific_user_123",
                    amount=250,
                    transaction_type="purchase",
                    credit_source="purchased",
                    order_id="order_xyz",
                    description="Purchased 250 credits via CCBill"
                )
        
        assert response.status_code == 200

    def test_usdt_credits_with_tx_hash_as_order_id(self, client: TestClient, monkeypatch):
        from app.services.auth_service import webhook_service
        
        with patch.object(webhook_service, "verify_usdt_signature", return_value=True):
            with patch("app.core.config.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.ccbill_client_secret = "test_secret"
                mock_get_settings.return_value = mock_settings
                
                with patch("app.routers.billing.credit_service.add_credits", new_callable=AsyncMock) as mock_add:
                    payload = {
                        "status": "confirmed",
                        "user_id": "user_456",
                        "credits": 100,
                        "tx_hash": "0xdef456",
                        "timestamp": time.time()
                    }
                    
                    response = client.post(
                        "/api/billing/webhooks/usdt",
                        json=payload,
                        headers={"X-Webhook-Signature": "sig"}
                    )
                    
                    call_args = mock_add.call_args
                    assert call_args.kwargs["order_id"] == "0xdef456"
                    assert "USDT" in call_args.kwargs["description"]
        
        assert response.status_code == 200


class TestStripeRefundWebhook:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_stripe_refund_processed(self, client: TestClient, monkeypatch):
        mock_result = {
            "status": "success",
            "user_id": "user_123",
            "credits_deducted": 100,
            "refund_id": "re_abc123"
        }
        
        with patch("app.services.billing_service.BillingService.handle_stripe_webhook", new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = mock_result
            
            payload = json.dumps({
                "id": "evt_refund",
                "type": "charge.refunded",
                "data": {
                    "object": {
                        "id": "ch_123",
                        "payment_intent": "pi_abc",
                        "amount_refunded": 499,
                        "refunds": {
                            "data": [{"id": "re_abc123", "reason": "requested_by_customer"}]
                        }
                    }
                }
            })
            
            response = client.post(
                "/api/billing/webhooks/stripe",
                content=payload,
                headers={"Stripe-Signature": "test_sig", "Content-Type": "application/json"}
            )
        
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_stripe_subscription_cancelled_via_webhook(self, client: TestClient, monkeypatch):
        mock_result = {"status": "cancelled", "user_id": "user_456"}
        
        with patch("app.services.billing_service.BillingService.handle_stripe_webhook", new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = mock_result
            
            payload = json.dumps({
                "id": "evt_cancel",
                "type": "customer.subscription.deleted",
                "data": {
                    "object": {
                        "id": "sub_xyz",
                        "customer": "cus_123",
                        "status": "canceled"
                    }
                }
            })
            
            response = client.post(
                "/api/billing/webhooks/stripe",
                content=payload,
                headers={"Stripe-Signature": "test_sig", "Content-Type": "application/json"}
            )
        
        assert response.status_code == 200

    def test_stripe_invoice_payment_succeeded_grants_monthly_credits(self, client: TestClient, monkeypatch):
        mock_result = {"status": "success", "user_id": "user_789", "credits_added": 100}
        
        with patch("app.services.billing_service.BillingService.handle_stripe_webhook", new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = mock_result
            
            payload = json.dumps({
                "id": "evt_invoice",
                "type": "invoice.payment_succeeded",
                "data": {
                    "object": {
                        "id": "in_123",
                        "customer": "cus_456",
                        "subscription": "sub_abc"
                    }
                }
            })
            
            response = client.post(
                "/api/billing/webhooks/stripe",
                content=payload,
                headers={"Stripe-Signature": "test_sig", "Content-Type": "application/json"}
            )
        
        assert response.status_code == 200
        assert response.json()["success"] is True
