import pytest
from fastapi.testclient import TestClient


class TestAuthRouter:
    
    def test_register_initiate(self, client: TestClient):
        response = client.post("/auth/register/initiate", json={"email": "test@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_verify_email(self, client: TestClient):
        response = client.post("/auth/verify-email", json={"code": "123456"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_resend_verification(self, client: TestClient):
        response = client.post("/auth/resend-verification", json={"email": "test@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_register(self, client: TestClient):
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "Test123!",
            "display_name": "Test User"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_current_user(self, client: TestClient):
        response = client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
    
    def test_update_profile(self, client: TestClient):
        response = client.put("/auth/me/profile", json={
            "display_name": "Updated Name",
            "bio": "Test bio"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_preferences(self, client: TestClient):
        response = client.put("/auth/me/preferences", json={
            "theme": "dark",
            "notifications": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_preferences(self, client: TestClient):
        response = client.get("/auth/me/preferences")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_checkin(self, client: TestClient):
        response = client.post("/auth/checkin")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_get_refill_status(self, client: TestClient):
        response = client.get("/auth/refill-status")
        assert response.status_code == 200
        data = response.json()
        assert "last_refill" in data or "next_refill" in data
    
    def test_complete_registration(self, client: TestClient):
        response = client.post("/auth/complete-registration", json={
            "display_name": "Test User"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_age_verification_start(self, client: TestClient):
        response = client.post("/auth/age-verification/start", json={
            "method": "id_card"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_age_verification_status(self, client: TestClient):
        response = client.get("/auth/age-verification/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "verified" in data
    
    def test_age_verification_webhook(self, client: TestClient):
        response = client.post("/auth/age-verification/webhook", json={
            "user_id": "test_user",
            "verified": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
