import pytest
from fastapi.testclient import TestClient


class TestSupportRouter:
    
    def test_create_support_ticket(self, client: TestClient):
        response = client.post("/api/billing/support", json={
            "subject": "Billing Issue",
            "message": "I have a billing problem",
            "category": "billing"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_support_tickets(self, client: TestClient):
        response = client.get("/api/billing/support")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_submit_feedback(self, client: TestClient):
        response = client.post("/api/billing/support/feedback", json={
            "rating": 5,
            "comment": "Great support!"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestAdminSupportRouter:
    
    def test_list_admin_tickets(self, client: TestClient):
        response = client.get("/admin/support-tickets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_resolve_ticket(self, client: TestClient):
        response = client.post("/admin/support-tickets/ticket_001/resolve", json={
            "resolution": "Issue resolved"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
