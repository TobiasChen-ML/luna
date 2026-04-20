import pytest
from fastapi.testclient import TestClient


class TestOpsRouter:
    
    def test_get_metrics_overview(self, client: TestClient):
        response = client.get("/api/ops/metrics/overview")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data or "health" in data
    
    def test_get_metrics_alerts(self, client: TestClient):
        response = client.get("/api/ops/metrics/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAdminOpsRouter:
    
    def test_get_admin_stats(self, client: TestClient):
        response = client.get("/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data or "characters" in data
    
    def test_get_chat_logs(self, client: TestClient):
        response = client.get("/admin/chat-logs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_audit_logs(self, client: TestClient):
        response = client.get("/admin/compliance/audit-logs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
