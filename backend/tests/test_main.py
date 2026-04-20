import pytest
from fastapi.testclient import TestClient


class TestMainApp:
    
    def test_health_check(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    def test_openapi_docs(self, client: TestClient):
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_json(self, client: TestClient):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
