import pytest
from fastapi.testclient import TestClient


class TestNotificationsRouter:
    
    def test_notifications_health(self, client: TestClient):
        response = client.get("/api/notifications/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_test_notification(self, client: TestClient):
        response = client.post("/api/notifications/test")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_subscribe_push(self, client: TestClient):
        response = client.post("/api/notifications/subscribe-push", json={
            "endpoint": "https://fcm.googleapis.com/test",
            "keys": {"p256dh": "test_key", "auth": "test_auth"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_unsubscribe_push(self, client: TestClient):
        response = client.delete("/api/notifications/unsubscribe-push")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_send_push_to_user(self, client: TestClient):
        response = client.post("/api/notifications/send-push/user_001", json={
            "title": "Test",
            "body": "Test notification"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_check_subscription(self, client: TestClient):
        response = client.get("/api/notifications/check-subscription")
        assert response.status_code == 200
        data = response.json()
        assert "subscribed" in data
