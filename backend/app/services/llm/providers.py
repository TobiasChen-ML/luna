import json
import logging
import copy
from typing import Optional, AsyncIterator, Any
import httpx
from . import BaseLLMProvider, LLMRequest, LLMResponse, StructuredResponse, Message

logger = logging.getLogger(__name__)


class NovitaLLMProvider(BaseLLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.novita.ai/openai", **kwargs):
        super().__init__(api_key, base_url, **kwargs)
        self.default_model = kwargs.get("default_model", "meta-llama/llama-3.3-70b-instruct")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.default_model
        body = self._build_openai_request(request)
        body["model"] = model
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=body
            )
            response.raise_for_status()
            data = response.json()
        
        choice = data["choices"][0]
        return LLMResponse(
            content=choice["message"]["content"],
            model=data.get("model", model),
            usage=data.get("usage", {}),
            finish_reason=choice.get("finish_reason", "stop")
        )
    
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        model = request.model or self.default_model
        body = self._build_openai_request(request)
        body["model"] = model
        body["stream"] = True
        
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
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
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
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