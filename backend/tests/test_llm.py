import pytest
from unittest.mock import AsyncMock, patch


class TestNovitaProvider:
    @pytest.mark.asyncio
    async def test_build_openai_request(self):
        from app.services.llm.providers import NovitaLLMProvider
        from app.services.llm import LLMRequest, Message
        
        provider = NovitaLLMProvider(
            api_key="test_key",
            base_url="https://api.novita.ai/v3/openai",
            default_model="test-model"
        )
        
        request = LLMRequest(
            messages=[Message(role="user", content="Hello")],
            temperature=0.7,
            max_tokens=100
        )
        
        body = provider._build_openai_request(request)
        
        assert body["temperature"] == 0.7
        assert body["max_tokens"] == 100
        assert len(body["messages"]) == 1
        assert body["messages"][0]["role"] == "user"

    def test_normalizes_v3_base_url(self):
        from app.services.llm.providers import NovitaLLMProvider

        provider = NovitaLLMProvider(
            api_key="test_key",
            base_url="https://api.novita.ai/v3",
        )

        assert provider.base_url == "https://api.novita.ai/openai/v1"

    def test_normalizes_v3_openai_base_url(self):
        from app.services.llm.providers import NovitaLLMProvider

        provider = NovitaLLMProvider(
            api_key="test_key",
            base_url="https://api.novita.ai/v3/openai",
        )

        assert provider.base_url == "https://api.novita.ai/openai/v1"

    def test_normalizes_openai_base_url_to_v1(self):
        from app.services.llm.providers import NovitaLLMProvider

        provider = NovitaLLMProvider(
            api_key="test_key",
            base_url="https://api.novita.ai/openai",
        )

        assert provider.base_url == "https://api.novita.ai/openai/v1"

    def test_normalizes_plain_novita_host_to_openai_v1(self):
        from app.services.llm.providers import NovitaLLMProvider

        provider = NovitaLLMProvider(
            api_key="test_key",
            base_url="https://api.novita.ai",
        )

        assert provider.base_url == "https://api.novita.ai/openai/v1"


class TestDeepseekProvider:
    def test_init(self):
        from app.services.llm.providers import DeepseekProvider
        
        provider = DeepseekProvider(
            api_key="test_key",
            default_model="deepseek-v3"
        )
        
        assert provider.default_model == "deepseek-v3"


class TestOllamaProvider:
    @pytest.mark.asyncio
    async def test_build_request(self):
        from app.services.llm.providers import OllamaProvider
        from app.services.llm import LLMRequest, Message
        
        provider = OllamaProvider(
            api_key="",
            base_url="http://localhost:11434",
            default_model="llama3"
        )
        
        request = LLMRequest(
            messages=[Message(role="user", content="Hello")],
            temperature=0.5,
            max_tokens=200
        )
        
        body = {
            "model": provider.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False
        }
        
        assert body["model"] == "llama3"
        assert len(body["messages"]) == 1


class TestLLMService:
    @pytest.mark.asyncio
    async def test_provider_registration(self):
        from app.services.llm_service import LLMService
        from unittest.mock import patch
        
        with patch.object(LLMService, '_init_providers'):
            service = LLMService()
            service._providers = {
                "novita": AsyncMock(),
                "deepseek": AsyncMock()
            }
            
            assert await service.get_provider("novita") is not None
            assert await service.get_provider("nonexistent") is None

    @pytest.mark.asyncio
    async def test_generate_stream_fallback_on_index_error(self):
        from app.services.llm_service import LLMService
        from app.services.llm import LLMResponse
        from unittest.mock import patch

        class BrokenStreamProvider:
            async def generate_stream(self, _request):
                raise IndexError("list index out of range")
                yield ""

            async def generate(self, _request):
                return LLMResponse(
                    content="fallback response",
                    model="test-model",
                    usage={},
                    finish_reason="stop",
                )

        with patch.object(LLMService, '_init_providers'):
            service = LLMService()
            service._providers = {"novita": BrokenStreamProvider()}

            chunks = []
            async for chunk in service.generate_stream(
                messages=[{"role": "user", "content": "hello"}],
                provider="novita",
            ):
                chunks.append(chunk)

            assert chunks == ["fallback response"]

    @pytest.mark.asyncio
    async def test_refresh_providers_uses_llm_base_url(self):
        from app.services.llm_service import LLMService
        from unittest.mock import patch

        async def mock_get_config_value(key, default=None):
            values = {
                "NOVITA_API_KEY": "novita-test-key",
                "LLM_BASE_URL": "https://api.novita.ai/openai/v1",
                "LLM_CHAT_MODEL": "test-primary-model",
                "LLM_ORCHESTRATOR_MODEL": "test-fallback-model",
                "LLM_API_KEY": "deepseek-test-key",
                "LLM_INTENT_MODEL": "deepseek-test-model",
            }
            return values.get(key, default)

        with patch.object(LLMService, "_init_providers"):
            service = LLMService()
            service._providers = {}

        with patch("app.services.llm_service.get_config_value", new=mock_get_config_value), \
             patch("app.services.llm_service.NovitaLLMProvider") as mock_novita:
            await service.refresh_providers()

            assert mock_novita.call_count == 1
            for call in mock_novita.call_args_list:
                assert call.kwargs["base_url"] == "https://api.novita.ai/openai/v1"
                assert call.kwargs["base_url"] != "http://localhost:11434"

    @pytest.mark.asyncio
    async def test_refresh_providers_uses_llm_api_key_for_novita_when_missing(self):
        from app.services.llm_service import LLMService
        from unittest.mock import patch

        async def mock_get_config_value(key, default=None):
            values = {
                "NOVITA_API_KEY": None,
                "LLM_API_KEY": "shared-test-key",
                "LLM_BASE_URL": "https://api.novita.ai/openai",
                "LLM_CHAT_MODEL": "test-primary-model",
                "LLM_ORCHESTRATOR_MODEL": "test-fallback-model",
                "LLM_INTENT_MODEL": "test-intent-model",
            }
            return values.get(key, default)

        with patch.object(LLMService, "_init_providers"):
            service = LLMService()
            service._providers = {}

        with patch("app.services.llm_service.get_config_value", new=mock_get_config_value), \
             patch("app.services.llm_service.NovitaLLMProvider") as mock_novita:
            await service.refresh_providers()

            assert mock_novita.call_count == 1
            for call in mock_novita.call_args_list:
                assert call.kwargs["api_key"] == "shared-test-key"
                assert call.kwargs["base_url"] == "https://api.novita.ai/openai"
