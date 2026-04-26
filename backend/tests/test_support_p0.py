from unittest.mock import AsyncMock


class TestSupportP0UserEndpoints:
    def test_create_support_ticket_contract(self, client, monkeypatch):
        from app.routers import support

        mock = AsyncMock(return_value={"id": "tkt_123", "status": "open"})
        monkeypatch.setattr(support.support_service, "create_ticket", mock)

        response = client.post(
            "/api/billing/support",
            json={
                "issue_type": "missed_credits",
                "description": "Payment succeeded but credits were not added.",
                "order_id": "ord_123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["id"] == "tkt_123"
        assert data["status"] == "open"

    def test_list_support_tickets_contract(self, client, monkeypatch):
        from app.routers import support

        mock = AsyncMock(
            return_value=[
                {
                    "id": "tkt_1",
                    "user_email": "test@example.com",
                    "order_id": "ord_1",
                    "issue_type": "other",
                    "message": "Example issue",
                    "status": "open",
                    "credits_granted": None,
                    "created_at": "2026-04-25T10:00:00",
                }
            ]
        )
        monkeypatch.setattr(support.support_service, "list_user_tickets", mock)

        response = client.get("/api/billing/support")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert data[0]["id"] == "tkt_1"

    def test_submit_feedback_accepts_profile_payload(self, client, monkeypatch):
        from app.routers import support

        monkeypatch.setattr(
            support.support_service,
            "submit_feedback",
            AsyncMock(return_value={"id": "tkt_fb_1", "status": "open"}),
        )
        response = client.post(
            "/api/billing/support/feedback",
            json={"feedback_type": "ux", "content": "The app experience is smooth and stable."},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True


class TestSupportP0AdminEndpoints:
    def test_list_admin_tickets_requires_admin(self, client):
        response = client.get("/admin/support-tickets")
        assert response.status_code == 403

    def test_list_admin_tickets_success(self, admin_client, monkeypatch):
        from app.routers import support

        monkeypatch.setattr(
            support.support_service,
            "list_admin_tickets",
            AsyncMock(return_value=[{"id": "tkt_1", "status": "open"}]),
        )
        response = admin_client.get("/admin/support-tickets?status=open")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_resolve_ticket_success(self, admin_client, monkeypatch):
        from app.routers import support

        monkeypatch.setattr(
            support.support_service,
            "resolve_ticket",
            AsyncMock(return_value={"id": "tkt_1", "status": "resolved"}),
        )
        response = admin_client.post(
            "/admin/support-tickets/tkt_1/resolve",
            json={"resolution": "Manually reconciled", "credits_granted": 20},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
