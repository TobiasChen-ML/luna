import hashlib
import hmac
import json
import urllib.parse

import pytest
from fastapi.testclient import TestClient


def build_telegram_init_data(bot_token: str, user: dict) -> str:
    params = {
        "auth_date": "1710000000",
        "query_id": "test-query",
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    params["hash"] = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    return urllib.parse.urlencode(params)


class TestIntegrationRouter:
    
    def test_list_templates(self, client: TestClient):
        response = client.get("/api/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_template(self, client: TestClient):
        response = client.get("/api/templates/template_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_list_blog_posts(self, client: TestClient):
        response = client.get("/api/blog")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_blog_post(self, client: TestClient):
        response = client.get("/api/blog/welcome-to-roxy")
        assert response.status_code == 200
        data = response.json()
        assert "slug" in data or "id" in data
    
    def test_create_blog_post(self, client: TestClient):
        response = client.post("/api/blog", json={
            "title": "Test Blog Post",
            "slug": "test-blog-post",
            "content": "Blog content here"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_blog_post(self, client: TestClient):
        response = client.put("/api/blog/post_001", json={
            "title": "Updated Blog Post"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_blog_post(self, client: TestClient):
        response = client.delete("/api/blog/post_001")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_admin_posts(self, client: TestClient):
        response = client.get("/api/blog/admin/posts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_upload_blog_image(self, client: TestClient):
        response = client.post("/api/blog/upload/image", json={
            "url": "https://example.com/image.jpg"
        })
        assert response.status_code == 200
        data = response.json()
        assert "url" in data
    
    def test_check_geo(self, client: TestClient):
        response = client.get("/api/geo/check")
        assert response.status_code == 200
        data = response.json()
        assert "country" in data or "allowed" in data
    
    def test_telegram_auth(self, client: TestClient, monkeypatch: pytest.MonkeyPatch):
        bot_token = "test-bot-token"

        async def fake_get_config_value(key: str, default=None):
            if key == "TELEGRAM_BOT_TOKEN":
                return bot_token
            return default

        monkeypatch.setattr("app.core.config.get_config_value", fake_get_config_value)
        init_data = build_telegram_init_data(
            bot_token,
            {
                "id": 123456,
                "username": "test_user",
                "first_name": "Test",
                "last_name": "User",
            },
        )

        response = client.post("/api/auth/telegram", json={
            "init_data": init_data,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["id"] == "telegram_123456"
    
    def test_get_creator(self, client: TestClient):
        response = client.get("/api/creators/user_001")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data or "username" in data
