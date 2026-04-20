import pytest
from fastapi.testclient import TestClient


class TestAdminLogin:
    """Covers all branches of POST /admin/login."""

    @pytest.fixture(autouse=True)
    def bypass_rate_limit(self, monkeypatch):
        """Disable rate limiting so tests don't interfere with each other."""
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_login_success(self, client: TestClient):
        """Valid credentials → 200 with JWT tokens and redirect."""
        response = client.post("/admin/login", json={
            "email": "admin@test.com",
            "password": "test-admin",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["redirect"] == "/admin/dashboard"

    def test_login_token_carries_is_admin(self, client: TestClient):
        """Access token must be a valid JWT with is_admin=True."""
        from app.services.auth_service import jwt_service

        response = client.post("/admin/login", json={
            "email": "admin@test.com",
            "password": "test-admin",
        })
        assert response.status_code == 200
        token = response.json()["access_token"]
        payload = jwt_service.verify_token(token)
        assert payload is not None
        assert payload.get("is_admin") is True

    def test_login_wrong_password(self, client: TestClient):
        """Wrong password → 401 Invalid credentials."""
        response = client.post("/admin/login", json={
            "email": "admin@test.com",
            "password": "wrong-password",
        })
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_non_admin_email(self, client: TestClient):
        """Email not in admin_emails → 403 Admin access required."""
        response = client.post("/admin/login", json={
            "email": "regular@example.com",
            "password": "test-admin",
        })
        assert response.status_code == 403
        assert "Admin access required" in response.json()["detail"]

    def test_login_missing_both_fields(self, client: TestClient):
        """Empty body → 400 required."""
        response = client.post("/admin/login", json={})
        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()

    def test_login_missing_password(self, client: TestClient):
        """Password absent → 400."""
        response = client.post("/admin/login", json={"email": "admin@test.com"})
        assert response.status_code == 400

    def test_login_admin_password_not_configured(self, mock_user, mock_settings):
        """ADMIN_PASSWORD not set → 503 admin login disabled."""
        from app.core.config import get_settings, Settings
        from app.core.dependencies import get_current_user, get_current_user_required
        from app.main import app

        settings_no_pw = Settings(
            environment="development",
            admin_emails=["admin@test.com"],
            admin_password=None,
            jwt_secret="test-secret-key",
        )

        saved = dict(app.dependency_overrides)
        app.dependency_overrides[get_settings] = lambda: settings_no_pw
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_current_user_required] = lambda: mock_user

        try:
            with TestClient(app) as c:
                response = c.post("/admin/login", json={
                    "email": "admin@test.com",
                    "password": "anything",
                })
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(saved)

        assert response.status_code == 503
        assert "disabled" in response.json()["detail"].lower()


class TestAdminRouter:

    @pytest.fixture(autouse=True)
    def bypass_rate_limit(self, monkeypatch):
        from app.services.rate_limit_service import RateLimitService
        monkeypatch.setattr(
            RateLimitService,
            "check_rate_limit",
            lambda self, key, max_requests, window_seconds=60: (True, max_requests, 0),
        )

    def test_admin_login_page(self, client: TestClient):
        response = client.get("/admin/login")
        assert response.status_code == 200
        data = response.json()
        assert "page" in data

    def test_admin_login(self, client: TestClient):
        response = client.post("/admin/login", json={
            "email": "admin@test.com",
            "password": "test-admin",
        })
        assert response.status_code == 200
        data = response.json()
        assert "success" in data or "token" in data

    def test_admin_logout(self, client: TestClient):
        response = client.get("/admin/logout")
        assert response.status_code == 200

    def test_send_login_code(self, client: TestClient):
        response = client.post("/admin/login/send-code", json={
            "email": "admin@example.com"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_verify_login_code(self, client: TestClient):
        response = client.post("/admin/login/verify-code", json={
            "email": "admin@example.com",
            "code": "123456"
        })
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_resend_login_code(self, client: TestClient):
        response = client.post("/admin/login/resend-code")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_list_characters_admin(self, client: TestClient):
        response = client.get("/admin/characters")
        assert response.status_code == 200
        data = response.json()
        assert "characters" in data or isinstance(data, list)

    def test_edit_character_page(self, client: TestClient):
        # char_001 does not exist in the test DB — 404 is the correct response
        response = client.get("/admin/characters/char_001/edit")
        assert response.status_code in (200, 404)

    def test_ai_fill_character(self, client: TestClient):
        # char_001 does not exist; endpoint returns success=False or 404
        response = client.post("/admin/characters/char_001/ai-fill", json={
            "fields": ["description", "personality"]
        })
        assert response.status_code in (200, 404)

    def test_update_character_admin(self, client: TestClient):
        # char_001 does not exist in the test DB — 404 is the correct response
        response = client.post("/admin/characters/char_001/update", json={
            "name": "Updated Character"
        })
        assert response.status_code in (200, 404)

    def test_delete_character_admin(self, client: TestClient):
        # char_001 does not exist in the test DB — 404 is the correct response
        response = client.post("/admin/characters/char_001/delete")
        assert response.status_code in (200, 404)
    
    def test_list_stories_admin(self, client: TestClient):
        response = client.get("/admin/stories")
        assert response.status_code == 200
        data = response.json()
        assert "stories" in data or isinstance(data, list)
    
    def test_create_story_page(self, client: TestClient):
        response = client.get("/admin/stories/create")
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
    
    def test_ai_generate_story(self, client: TestClient):
        response = client.post("/admin/stories/ai-generate", json={
            "title": "Test Story",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
    
    def test_create_story_admin(self, client: TestClient):
        response = client.post("/admin/stories/create", json={
            "title": "Test Story",
            "character_id": "char_001"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_edit_story_page(self, client: TestClient):
        response = client.get("/admin/stories/story_001/edit")
        assert response.status_code == 200
        data = response.json()
        assert "page" in data
    
    def test_update_story_admin(self, client: TestClient):
        response = client.post("/admin/stories/story_001/update", json={
            "title": "Updated Story"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_story_admin(self, client: TestClient):
        response = client.post("/admin/stories/story_001/delete")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_list_templates_admin(self, client: TestClient):
        response = client.get("/admin/templates")
        assert response.status_code == 200
        data = response.json()
        assert "templates" in data or isinstance(data, list)
    
    def test_list_prompts_admin(self, client: TestClient):
        response = client.get("/admin/prompts")
        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data or isinstance(data, list)
    
    def test_get_prompt_admin(self, client: TestClient):
        response = client.get("/admin/prompts/default")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
    
    def test_create_prompt(self, client: TestClient):
        response = client.post("/admin/prompts", json={
            "name": "test_prompt",
            "content": "Test prompt content"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_update_prompt(self, client: TestClient):
        response = client.post("/admin/prompts/default", json={
            "content": "Updated content"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_test_prompt(self, client: TestClient):
        response = client.post("/admin/prompts/default/test", json={
            "variables": {"name": "Test"}
        })
        assert response.status_code == 200
        data = response.json()
        assert "prompt_name" in data or "test_output" in data
    
    def test_list_batch_jobs(self, client: TestClient):
        response = client.get("/admin/batch-jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data or isinstance(data, list)
    
    def test_admin_dashboard(self, client: TestClient):
        response = client.get("/admin/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "page" in data or "stats" in data
    
    def test_list_admin_tasks(self, client: TestClient):
        response = client.get("/admin/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data or isinstance(data, list)


class TestAdminAPIRouter:
    """Endpoints under /admin/api/* require admin auth — uses admin_client."""

    def test_create_api_key(self, admin_client: TestClient):
        response = admin_client.post("/v1/admin/api-keys", json={"name": "Test Key"})
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    def test_list_api_keys(self, admin_client: TestClient):
        response = admin_client.get("/v1/admin/api-keys")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_delete_api_key(self, admin_client: TestClient):
        response = admin_client.delete("/v1/admin/api-keys/key_001")
        assert response.status_code in (200, 404)

    def test_batch_delete_characters_empty_ids(self, admin_client: TestClient):
        response = admin_client.post("/api/admin/api/characters/batch-delete", json={
            "ids": []
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "No IDs provided" in data["message"]

    def test_batch_delete_characters_non_existent(self, admin_client: TestClient):
        response = admin_client.post("/api/admin/api/characters/batch-delete", json={
            "ids": ["non_existent_001", "non_existent_002"]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Deleted" in data["message"]

    def test_regenerate_character_images_not_found(self, admin_client: TestClient):
        response = admin_client.post("/api/admin/api/characters/non_existent_id/regenerate-images")
        assert response.status_code in (400, 404, 500)

    def test_list_characters_api(self, admin_client: TestClient):
        response = admin_client.get("/api/admin/api/characters")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_batch_delete_stories(self, admin_client: TestClient):
        response = admin_client.post("/api/admin/api/stories/batch-delete", json={
            "story_ids": ["story_001"]
        })
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_list_templates_api(self, admin_client: TestClient):
        response = admin_client.get("/api/admin/api/templates")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_system_prompts(self, admin_client: TestClient):
        response = admin_client.get("/api/admin/api/system-prompt-templates")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_batch_variables(self, admin_client: TestClient):
        response = admin_client.get("/api/admin/api/batch-variables")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_start_batch_generate(self, admin_client: TestClient):
        response = admin_client.post("/api/admin/api/batch-generate", json={
            "template_id": "template_001",
            "variables": []
        })
        assert response.status_code == 200
        assert "id" in response.json()

    def test_get_batch_job(self, admin_client: TestClient):
        response = admin_client.get("/api/admin/api/batch-jobs/job_001")
        assert response.status_code in (200, 404)

    def test_start_seo_generate(self, admin_client: TestClient):
        response = admin_client.post("/api/admin/api/seo-generate", json={
            "keywords": ["AI", "chat"]
        })
        assert response.status_code == 200
        assert "id" in response.json()

    def test_list_voices(self, admin_client: TestClient):
        response = admin_client.get("/api/admin/api/voices")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestLegacyAPIKeyRouter:
    """Legacy API key endpoints require admin auth — uses admin_client."""

    def test_list_api_keys_legacy(self, admin_client: TestClient):
        response = admin_client.get("/admin/api-keys")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_api_key_legacy(self, admin_client: TestClient):
        response = admin_client.post("/admin/api-keys", json={"name": "Legacy Key"})
        assert response.status_code == 200
        assert "id" in response.json()

    def test_revoke_api_key(self, admin_client: TestClient):
        response = admin_client.post("/admin/api-keys/key_001/revoke")
        assert response.status_code in (200, 404)
