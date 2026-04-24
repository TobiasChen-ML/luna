import json
import logging
import copy
from typing import Optional, AsyncIterator, Any
import httpx
from . import BaseLLMProvider, LLMRequest, LLMResponse, StructuredResponse, Message

logger = logging.getLogger(__name__)


class NovitaLLMProvider(BaseLLMProvider):
    _NOVITA_MODEL_FALLBACKS = [
        "meta-llama/llama-3.3-70b-instruct",
        "google/gemma-4-26b-a4b-it",
        "sao10k/l3-8b-lunaris",
    ]

    def __init__(self, api_key: str, base_url: str = "https://api.novita.ai/openai/v1", **kwargs):
        super().__init__(api_key, self._normalize_base_url(base_url), **kwargs)
        self.default_model = kwargs.get("default_model", "meta-llama/llama-3.3-70b-instruct")
        self._known_missing_models: set[str] = set()

    @staticmethod
    def _normalize_base_url(base_url: str) -> str:
        normalized = base_url.rstrip("/")

        # Provider methods append "/chat/completions". Accept full endpoint input too.
        if normalized.endswith("/chat/completions"):
            normalized = normalized[: -len("/chat/completions")]

        # Normalize Novita OpenAI-compatible URLs to ".../openai/v1".
        if normalized.startswith("https://api.novita.ai") or normalized.startswith("http://api.novita.ai"):
            if normalized.endswith("/openai/v1"):
                return normalized
            if normalized.endswith("/v1/openai"):
                return normalized[: -len("/v1/openai")] + "/openai/v1"
            if normalized.endswith("/v3/openai/v1"):
                return normalized[: -len("/v3/openai/v1")] + "/openai/v1"
            if normalized.endswith("/v3/openai"):
                return normalized[: -len("/v3/openai")] + "/openai/v1"
            if normalized.endswith("/openai"):
                return normalized + "/v1"
            if normalized.endswith("/v3"):
                return normalized[: -len("/v3")] + "/openai/v1"
            if normalized.endswith("api.novita.ai"):
                return normalized + "/openai/v1"

        return normalized

    @staticmethod
    def _is_model_not_found(exc: Exception) -> bool:
        if not isinstance(exc, httpx.HTTPStatusError):
            return False
        return exc.response.status_code == 404

    @staticmethod
    def _is_retriable_model_error(exc: Exception) -> bool:
        """Retry with fallback model for model-specific 400/404 errors."""
        if NovitaLLMProvider._is_model_not_found(exc):
            return True
        if not isinstance(exc, httpx.HTTPStatusError):
            return False
        if exc.response.status_code != 400:
            return False
        try:
            detail = (exc.response.text or "").lower()
        except Exception:
            return False
        model_markers = ("model", "engine", "deployment")
        missing_markers = ("not found", "does not exist", "invalid", "unsupported", "unavailable")
        return any(m in detail for m in model_markers) and any(m in detail for m in missing_markers)

    def _candidate_models(self, requested_model: Optional[str]) -> list[str]:
        ordered: list[str] = []
        for model in [requested_model, self.default_model, *self._NOVITA_MODEL_FALLBACKS]:
            if model and model not in ordered and model not in self._known_missing_models:
                ordered.append(model)
        return ordered

    @staticmethod
    def _error_excerpt(exc: Exception) -> str:
        if not isinstance(exc, httpx.HTTPStatusError):
            return str(exc)
        try:
            text = exc.response.text or ""
            text = text.strip().replace("\n", " ")
            return text[:280]
        except Exception:
            return str(exc)
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        body = self._build_openai_request(request)
        endpoint = f"{self.base_url}/chat/completions"
        last_error: Optional[Exception] = None
        selected_model: Optional[str] = None
        data: Optional[dict] = None

        async with httpx.AsyncClient(timeout=120) as client:
            for model in self._candidate_models(request.model):
                body["model"] = model
                try:
                    response = await client.post(
                        endpoint,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=body
                    )
                    response.raise_for_status()
                    data = response.json()
                    selected_model = model
                    break
                except Exception as exc:
                    last_error = exc
                    if self._is_retriable_model_error(exc):
                        self._known_missing_models.add(model)
                        logger.warning(
                            "Novita model unavailable for endpoint=%s model=%s; trying fallback model. detail=%s",
                            endpoint,
                            model,
                            self._error_excerpt(exc),
                        )
                        continue
                    raise

        if data is None or selected_model is None:
            assert last_error is not None
            raise last_error

        choices = data.get("choices") or []
        if not choices:
            raise ValueError(f"LLM response missing choices: {data}")

        choice = choices[0]
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", selected_model),
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop")
        )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        body = self._build_openai_request(request)
        body["stream"] = True
        endpoint = f"{self.base_url}/chat/completions"
        last_error: Optional[Exception] = None

        async with httpx.AsyncClient(timeout=120) as client:
            for model in self._candidate_models(request.model):
                body["model"] = model
                try:
                    async with client.stream(
                        "POST",
                        endpoint,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json=body
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    return
                                try:
                                    data = json.loads(data_str)
                                    choices = data.get("choices") or []
                                    if not choices:
                                        continue
                                    delta = choices[0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
                        return
                except Exception as exc:
                    last_error = exc
                    if self._is_retriable_model_error(exc):
                        self._known_missing_models.add(model)
                        logger.warning(
                            "Novita stream model unavailable for endpoint=%s model=%s; trying fallback model. detail=%s",
                            endpoint,
                            model,
                            self._error_excerpt(exc),
                        )
                        continue
                    raise

        if last_error:
            raise last_error
    
    async def generate_structured(
        self,
        request: LLMRequest,
        schema: dict
    ) -> StructuredResponse:
        messages = [
            Message(role=m.role, content=m.content) if isinstance(m, Message) else Message(**m)
            for m in request.messages
        ]
        
        system_message = Message(
            role="system",
            content=f"You must respond with valid JSON matching this schema: {json.dumps(schema)}"
        )
        
        new_request = LLMRequest(
            messages=[system_message] + messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            response_format={"type": "json_object"}
        )
        
        response = await self.generate(new_request)
        
        try:
            data = json.loads(response.content)
            return StructuredResponse(data=data, raw_content=response.content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return StructuredResponse(data={}, raw_content=response.content)


class DeepseekProvider(NovitaLLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.default_model = kwargs.get("default_model", "deepseek/deepseek-v3.2")


class OpenAIProvider(NovitaLLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.default_model = kwargs.get("default_model", "gpt-4o")


class OllamaProvider(BaseLLMProvider):
    def __init__(self, api_key: str = "", base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.default_model = kwargs.get("default_model", "llama3")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.default_model
        
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }
        
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=body
            )
            response.raise_for_status()
            data = response.json()
        
        return LLMResponse(
            content=data["message"]["content"],
            model=model,
            usage={},
            finish_reason="stop"
        )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        model = request.model or self.default_model
        
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens
            }
        }
        
        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=body
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                    except json.JSONDecodeError:
                        continue
    
    async def generate_structured(
        self,
        request: LLMRequest,
        schema: dict
    ) -> StructuredResponse:
        messages = [
            Message(role=m.role, content=m.content) if isinstance(m, Message) else Message(**m)
            for m in request.messages
        ]
        
        system_message = Message(
            role="system",
            content=f"Respond ONLY with valid JSON matching: {json.dumps(schema)}"
        )
        
        new_request = LLMRequest(
            messages=[system_message] + messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        response = await self.generate(new_request)
        
        try:
            data = json.loads(response.content)
            return StructuredResponse(data=data, raw_content=response.content)
        except json.JSONDecodeError:
            return StructuredResponse(data={}, raw_content=response.content)
