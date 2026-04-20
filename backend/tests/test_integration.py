import pytest
from fastapi.testclient import TestClient


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
    
    def test_telegram_auth(self, client: TestClient):
        response = client.post("/api/auth/telegram", json={
            "id": "telegram_user_001",
            "username": "test_user"
        })
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "token" in data
    
    def test_get_creator(self, client: TestClient):
        response = client.get("/api/creators/user_001")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data or "username" in data
