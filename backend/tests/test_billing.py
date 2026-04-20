import pytest
from fastapi.testclient import TestClient


class TestBillingRouter:
    
    def test_get_pricing(self, client: TestClient):
        response = client.get("/api/billing/pricing")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_subscription_checkout(self, client: TestClient):
        response = client.post("/api/billing/subscriptions/checkout", json={
            "tier": "premium",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel"
        })
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data or "session_id" in data
    
    def test_subscription_portal(self, client: TestClient):
        response = client.post("/api/billing/subscriptions/portal")
        assert response.status_code == 200
        data = response.json()
        assert "portal_url" in data
    
    def test_get_current_subscription(self, client: TestClient):
        response = client.get("/api/billing/subscriptions/current")
        assert response.status_code == 200
        data = response.json()
        assert "tier" in data or "status" in data
    
    def test_cancel_subscription(self, client: TestClient):
        response = client.post("/api/billing/subscriptions/cancel")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_reactivate_subscription(self, client: TestClient):
        response = client.post("/api/billing/subscriptions/reactivate")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_credit_packs(self, client: TestClient):
        response = client.get("/api/billing/credit-packs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_credit_pack_checkout(self, client: TestClient):
        response = client.post("/api/billing/credit-packs/checkout", json={
            "pack_type": "medium",
            "success_url": "https://example.com/success",
            "cancel_url": "https://example.com/cancel"
        })
        assert response.status_code == 200
        data = response.json()
        assert "checkout_url" in data or "session_id" in data
    
    def test_get_credits_balance(self, client: TestClient):
        response = client.get("/api/billing/credits/balance")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
    
    def test_get_billing_history(self, client: TestClient):
        response = client.get("/api/billing/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_create_usdt_order(self, client: TestClient):
        response = client.post("/api/billing/usdt/orders", json={
            "amount": 10.0,
            "product_id": "credits_100"
        })
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
    
    def test_get_usdt_order(self, client: TestClient):
        response = client.get("/api/billing/usdt/orders/order_001")
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
    
    def test_submit_usdt_order(self, client: TestClient):
        response = client.post("/api/billing/usdt/orders/order_001/submit")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_refresh_usdt_order(self, client: TestClient):
        response = client.post("/api/billing/usdt/orders/order_001/refresh")
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
    
    def test_create_telegram_stars_order(self, client: TestClient):
        response = client.post("/api/billing/telegram-stars/orders", json={
            "amount": 100,
            "product_id": "credits_50"
        })
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
    
    def test_get_telegram_stars_order(self, client: TestClient):
        response = client.get("/api/billing/telegram-stars/orders/order_001")
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
    
    def test_submit_telegram_stars_order(self, client: TestClient):
        response = client.post("/api/billing/telegram-stars/orders/order_001/submit")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_ccbill_webhook(self, client: TestClient):
        response = client.post("/api/billing/webhooks/ccbill", json={
            "event": "payment_success"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_usdt_webhook(self, client: TestClient):
        response = client.post("/api/billing/webhooks/usdt", json={
            "tx_hash": "0x123",
            "status": "confirmed"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_telegram_stars_webhook(self, client: TestClient):
        response = client.post("/api/billing/webhooks/telegram-stars", json={
            "order_id": "order_001",
            "status": "paid"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_stripe_webhook_missing_signature(self, client: TestClient):
        response = client.post("/api/billing/webhooks/stripe", json={
            "type": "checkout.session.completed"
        })
        assert response.status_code == 401
    
    def test_stripe_webhook_invalid_signature(self, client: TestClient):
        response = client.post(
            "/api/billing/webhooks/stripe",
            content=b'{"type": "checkout.session.completed"}',
            headers={"Stripe-Signature": "invalid_signature"}
        )
        assert response.status_code in [400, 401]


class TestBillingService:
    
    @pytest.mark.asyncio
    async def test_handle_checkout_completed_credit_pack(self):
        from app.services.billing_service import BillingService
        
        billing_svc = BillingService()
        
        session_data = {
            "mode": "payment",
            "metadata": {
                "user_id": "test_user_123",
                "credits": 100
            },
            "payment_intent": "pi_test_123"
        }
        
        result = await billing_svc._handle_checkout_completed(session_data)
        
        assert result["status"] in ["success", "error"]
    
    @pytest.mark.asyncio
    async def test_handle_subscription_payment(self):
        from app.services.billing_service import BillingService
        
        billing_svc = BillingService()
        
        invoice_data = {
            "customer": "cus_test_123",
            "subscription": "sub_test_123",
            "period_end": 1735689600
        }
        
        result = await billing_svc._handle_subscription_payment(invoice_data)
        
        assert result["status"] in ["success", "error"]
    
    @pytest.mark.asyncio
    async def test_handle_subscription_cancelled(self):
        from app.services.billing_service import BillingService
        
        billing_svc = BillingService()
        
        subscription_data = {
            "customer": "cus_test_123",
            "status": "canceled"
        }
        
        result = await billing_svc._handle_subscription_cancelled(subscription_data)
        
        assert result["status"] in ["cancelled", "error"]
    
    @pytest.mark.asyncio
    async def test_handle_subscription_created(self):
        from app.services.billing_service import BillingService
        
        billing_svc = BillingService()
        
        subscription_data = {
            "customer": "cus_test_123",
            "status": "active",
            "current_period_end": 1735689600
        }
        
        result = await billing_svc._handle_subscription_created(subscription_data)
        
        assert result["status"] in ["success", "ignored", "error"]


class TestSchedulerService:
    
    def test_init_scheduler(self):
        from app.services.scheduler_service import init_scheduler, shutdown_scheduler
        
        scheduler = init_scheduler()
        assert scheduler is not None
        
        jobs = scheduler.get_jobs()
        job_ids = [job.id for job in jobs]
        
        assert "check_subscription_expiry" in job_ids
        assert "grant_monthly_credits" in job_ids
        
        shutdown_scheduler()
    
    def test_start_scheduler(self):
        from app.services.scheduler_service import init_scheduler, shutdown_scheduler, scheduler as sched_module
        
        shutdown_scheduler()
        
        scheduler = init_scheduler()
        assert scheduler is not None
        
        jobs = scheduler.get_jobs()
        assert len(jobs) >= 2
        
        shutdown_scheduler()
    
    @pytest.mark.asyncio
    async def test_check_subscription_expiry(self):
        from app.services.scheduler_service import check_subscription_expiry
        
        await check_subscription_expiry()
    
    @pytest.mark.asyncio
    async def test_grant_monthly_credits_job(self):
        from app.services.scheduler_service import grant_monthly_credits_job
        
        await grant_monthly_credits_job()
