import pytest
import asyncio
from typing import Generator, AsyncGenerator
from httpx import AsyncClient, ASGITransport
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
def mock_user():
    from app.core.dependencies import MockUser
    return MockUser(user_id="test_user_001", email="test@example.com", is_admin=False)


@pytest.fixture(scope="module")
def mock_admin_user():
    from app.core.dependencies import MockUser
    return MockUser(user_id="test_admin_001", email="admin@test.com", is_admin=True)


@pytest.fixture(scope="module")
def mock_settings():
    from app.core.config import Settings
    return Settings(
        app_name="Test Roxy API",
        debug=True,
        environment="development",
        database_url="sqlite:///./test_roxy.db",
        redis_url="redis://localhost:6379/15",
        firebase_project_id="test-project",
        novita_api_key="test-novita-key",
        novita_base_url="https://api.novita.ai/v3",
        llm_api_key="test-llm-key",
        llm_base_url="https://api.novita.ai/v3/openai",
        llm_primary_model="test-model",
        llm_fallback_model="test-fallback",
        llm_structured_model="test-structured",
        llm_timeout=120,
        elevenlabs_api_key="test-elevenlabs-key",
        stripe_secret_key="sk_test_123",
        admin_password="test-admin",
        admin_emails=["admin@test.com"],
        jwt_secret="test-secret-key",
    )


@pytest.fixture(scope="module")
def client(mock_user, mock_settings) -> Generator:
    from app.core.dependencies import get_current_user, get_current_user_required
    from app.core.config import get_settings

    async def override_get_current_user():
        return mock_user

    async def override_get_current_user_required():
        return mock_user

    def override_get_settings():
        return mock_settings

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_required] = override_get_current_user_required
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def admin_client(mock_admin_user, mock_settings) -> Generator:
    """Client where every request is authenticated as an admin user."""
    from app.core.dependencies import (
        get_current_user, get_current_user_required, get_admin_user
    )
    from app.core.config import get_settings

    async def override_admin():
        return mock_admin_user

    def override_get_settings():
        return mock_settings

    app.dependency_overrides[get_current_user] = override_admin
    app.dependency_overrides[get_current_user_required] = override_admin
    app.dependency_overrides[get_admin_user] = override_admin
    app.dependency_overrides[get_settings] = override_get_settings

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
async def async_client() -> AsyncGenerator:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


@pytest.fixture
def mock_user_id() -> str:
    return "test_user_001"


@pytest.fixture
def mock_character_id() -> str:
    return "test_char_001"


@pytest.fixture
def mock_session_id() -> str:
    return "test_session_001"


@pytest.fixture
def mock_story_id() -> str:
    return "test_story_001"


@pytest.fixture
def mock_task_id() -> str:
    return "test_task_001"


@pytest.fixture
def auth_headers() -> dict:
    return {"Authorization": "Bearer test_token"}


@pytest.fixture
def mock_redis():
    redis_mock = MagicMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.set = AsyncMock(return_value=True)
    redis_mock.delete = AsyncMock(return_value=True)
    redis_mock.publish = AsyncMock(return_value=True)
    redis_mock.subscribe = AsyncMock()
    redis_mock.lpush = AsyncMock(return_value=1)
    redis_mock.lrange = AsyncMock(return_value=[])
    redis_mock.get_task_cache = AsyncMock(return_value=None)
    redis_mock.set_task_cache = AsyncMock(return_value=True)
    return redis_mock


@pytest.fixture
def mock_db():
    db_mock = MagicMock()
    db_mock.get_session = MagicMock()
    db_mock.execute = AsyncMock(return_value=None)
    db_mock.connect = AsyncMock()
    return db_mock


@pytest.fixture
def mock_firebase():
    firebase_mock = MagicMock()
    firebase_mock.verify_token = MagicMock(return_value={"uid": "test-user-123", "email": "test@example.com"})
    firebase_mock.get_user_by_uid = MagicMock(return_value=None)
    firebase_mock.create_user = MagicMock(return_value=MagicMock(uid="test-user-123", email="test@example.com"))
    return firebase_mock


@pytest.fixture
def mock_httpx_client():
    client_mock = MagicMock()
    client_mock.post = AsyncMock()
    client_mock.get = AsyncMock()
    client_mock.stream = AsyncMock()
    client_mock.aclose = AsyncMock()
    return client_mock


@pytest.fixture
def mock_task_service():
    task_mock = MagicMock()
    task_mock.create_task = AsyncMock()
    task_mock.get_task = AsyncMock()
    task_mock.update_task = AsyncMock()
    task_mock.handle_webhook = AsyncMock()
    return task_mock


@pytest.fixture(autouse=True)
def mock_llm_service():
    from app.services.llm_service import LLMService
    from app.services.llm import LLMResponse
    
    mock_service = MagicMock(spec=LLMService)
    mock_service.generate = AsyncMock(return_value=LLMResponse(
        content="Test response",
        model="test-model",
        finish_reason="stop",
        usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    ))
    mock_service.generate_stream = AsyncMock(return_value=iter(["Test ", "response"]))
    mock_service.generate_structured = AsyncMock(return_value={"result": "test"})
    mock_service.get_provider = MagicMock(return_value=MagicMock())
    
    LLMService._instance = mock_service
    
    yield mock_service
    
    LLMService._instance = None


@pytest.fixture(autouse=True)
def mock_media_service(mock_settings):
    from app.services.media_service import MediaService
    from app.services.media import NovitaImageProvider, ImageGenerationResult

    mock_service = MagicMock(spec=MediaService)

    novita_provider = NovitaImageProvider(
        api_key=mock_settings.novita_api_key,
        base_url=mock_settings.novita_base_url
    )

    mock_service._image_providers = {"novita": novita_provider}
    mock_service.get_image_provider = MagicMock(
        side_effect=lambda name=None: (
            mock_service._image_providers.get(name) if name
            else next(iter(mock_service._image_providers.values()), None)
        )
    )

    async def mock_generate_image(prompt, **kwargs):
        return ImageGenerationResult(image_url="https://novita.ai/test_image.png")

    mock_service.generate_image = mock_generate_image
    
    MediaService._instance = mock_service
    
    yield mock_service
    
    MediaService._instance = None


@pytest.fixture
def admin_jwt_token(mock_admin_user, mock_settings):
    from app.services.auth_service import JWTService
    jwt_service = JWTService()
    return jwt_service.create_access_token(
        user_id=mock_admin_user.id,
        email=mock_admin_user.email,
        is_admin=True
    )


@pytest.fixture
def mock_character_factory_dependencies():
    from unittest.mock import patch, MagicMock, AsyncMock
    from app.services.llm import LLMResponse
    
    patches = []
    created_characters = []
    
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value=LLMResponse(
        content='{"description": "A test character", "greeting": "Hello!", "personality_summary": "Friendly"}',
        model="test-model",
        finish_reason="stop",
        usage={}
    ))
    
    mock_media = MagicMock()
    mock_media.generate_image = AsyncMock(return_value=MagicMock(image_url="https://example.com/test.png"))
    
    mock_upload = AsyncMock(return_value="https://r2.example.com/test.png")
    
    async def _create_character_impl(data):
        import random
        import string
        from app.models.character import generate_character_id, generate_slug
        
        char_id = generate_character_id()
        slug = data.slug or generate_slug(data.name)
        
        char = {
            "id": char_id,
            "name": data.name,
            "slug": slug,
            "description": data.description,
            "greeting": data.greeting,
            "template_id": data.template_id,
            "generation_mode": data.generation_mode,
            "personality_tags": data.personality_tags or [],
            "age": data.age,
        }
        created_characters.append(char)
        return char
    
    mock_create_character = AsyncMock(side_effect=_create_character_impl)
    
    llm_patch = patch("app.services.character_factory.CharacterFactory._get_llm_service", return_value=mock_llm)
    media_patch = patch("app.services.character_factory.CharacterFactory._get_media_service", return_value=mock_media)
    upload_patch = patch("app.services.storage_service.storage_service.upload_from_url", mock_upload)
    create_patch = patch("app.services.character_service.character_service.create_character", mock_create_character)
    
    patches.append(llm_patch)
    patches.append(media_patch)
    patches.append(upload_patch)
    patches.append(create_patch)
    
    for p in patches:
        p.start()
    
    yield {
        "llm": mock_llm,
        "media": mock_media,
        "upload": mock_upload,
        "create_character": mock_create_character,
        "created_characters": created_characters,
    }
    
    for p in patches:
        p.stop()
    created_characters.clear()


@pytest.fixture
async def async_admin_client(admin_jwt_token, mock_settings):
    from app.core.dependencies import get_admin_user, get_settings
    from app.core.dependencies import MockUser
    
    mock_admin = MockUser(user_id="test_admin_001", email="admin@test.com", is_admin=True)
    
    async def override_admin():
        return mock_admin
    
    def override_get_settings():
        return mock_settings
    
    app.dependency_overrides[get_admin_user] = override_admin
    app.dependency_overrides[get_settings] = override_get_settings
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    
    app.dependency_overrides.clear()
