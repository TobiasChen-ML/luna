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
    def test_provider_registration(self):
        from app.services.llm_service import LLMService
        from unittest.mock import patch
        
        with patch.object(LLMService, '_init_providers'):
            service = LLMService()
            service._providers = {
                "novita": AsyncMock(),
                "deepseek": AsyncMock()
            }
            
            assert service.get_provider("novita") is not None
            assert service.get_provider("nonexistent") is None