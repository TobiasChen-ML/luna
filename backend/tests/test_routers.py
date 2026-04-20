import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock


@pytest.fixture
def app():
    from app.main import app
    return app


@pytest.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_register_initiate(self, client):
        response = await client.post(
            "/api/auth/register/initiate",
            json={"email": "test@example.com", "password": "Test123!", "display_name": "Test User"}
        )
        assert response.status_code in [200, 400, 409]

    @pytest.mark.asyncio
    async def test_get_current_user(self, client):
        response = await client.get("/api/auth/me")
        assert response.status_code in [200, 401]


class TestChatEndpoints:
    @pytest.mark.asyncio
    async def test_get_sessions(self, client):
        response = await client.get("/api/chat/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "sessions" in data

    @pytest.mark.asyncio
    async def test_create_session(self, client):
        response = await client.post(
            "/api/chat/sessions",
            json={"character_id": "char_001"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_session_messages(self, client):
        response = await client.get("/api/chat/sessions/session_001/messages")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "messages" in data


class TestMediaEndpoints:
    @pytest.mark.asyncio
    async def test_generate_image_async(self, client):
        response = await client.post(
            "/api/images/generate-async",
            json={"prompt": "test image"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_task(self, client):
        response = await client.get("/api/images/tasks/task_001")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data


class TestNotificationEndpoints:
    @pytest.mark.asyncio
    async def test_notifications_health(self, client):
        response = await client.get("/api/notifications/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"