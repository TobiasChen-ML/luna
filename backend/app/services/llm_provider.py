import httpx
import json
from typing import Optional, AsyncIterator, Any
from abc import ABC, abstractmethod

from app.core.config import settings, get_config_value
from app.core.exceptions import ProviderError
from app.models import ChatMessage


class BaseLLMProvider(ABC):
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=settings.llm_timeout)

    async def close(self):
        await self.client.aclose()

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> dict[str, Any]:
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        pass

    @abstractmethod
    async def structured_output(
        self,
        messages: list[ChatMessage],
        model: str,
        schema: dict[str, Any],
        **kwargs,
    ) -> dict[str, Any]:
        pass


class OpenAICompatibleProvider(BaseLLMProvider):
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> dict[str, Any]:
        formatted_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs,
            },
        )
        
        if response.status_code != 200:
            raise ProviderError(f"LLM API error: {response.text}")
        
        return response.json()

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        formatted_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
                **kwargs,
            },
        ) as response:
            if response.status_code != 200:
                raise ProviderError(f"LLM API error: {await response.aread()}")
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if content := chunk.get("choices", [{}])[0].get("delta", {}).get("content"):
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def structured_output(
        self,
        messages: list[ChatMessage],
        model: str,
        schema: dict[str, Any],
        **kwargs,
    ) -> dict[str, Any]:
        formatted_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        
        response = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": formatted_messages,
                "response_format": {"type": "json_object"},
                **kwargs,
            },
        )
        
        if response.status_code != 200:
            raise ProviderError(f"LLM API error: {response.text}")
        
        result = response.json()
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
        return json.loads(content)


class NovitaProvider(OpenAICompatibleProvider):
    def __init__(self):
        super().__init__(
            api_key=settings.novita_api_key or "",
            base_url=settings.novita_base_url,
        )

    async def _resolve_api_key(self) -> str:
        return await get_config_value("NOVITA_API_KEY", self.api_key) or self.api_key


class DeepSeekProvider(OpenAICompatibleProvider):
    def __init__(self):
        super().__init__(
            api_key=settings.llm_api_key,
            base_url="https://api.deepseek.com/v1",
        )


class OllamaProvider(BaseLLMProvider):
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> dict[str, Any]:
        formatted_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        
        response = await self.client.post(
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": formatted_messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        
        if response.status_code != 200:
            raise ProviderError(f"Ollama error: {response.text}")
        
        return response.json()

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncIterator[str]:
        formatted_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/chat",
            json={
                "model": model,
                "messages": formatted_messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        ) as response:
            async for line in response.aiter_lines():
                try:
                    chunk = json.loads(line)
                    if content := chunk.get("message", {}).get("content"):
                        yield content
                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

    async def structured_output(
        self,
        messages: list[ChatMessage],
        model: str,
        schema: dict[str, Any],
        **kwargs,
    ) -> dict[str, Any]:
        messages_with_instruction = list(messages)
        messages_with_instruction.append(
            ChatMessage(
                role="system",
                content=f"Respond with a valid JSON object matching this schema: {json.dumps(schema)}",
            )
        )
        
        result = await self.chat(messages_with_instruction, model, **kwargs)
        content = result.get("message", {}).get("content", "{}")
        return json.loads(content)


def get_llm_provider(provider: str = "novita") -> BaseLLMProvider:
    providers = {
        "novita": NovitaProvider,
        "deepseek": DeepSeekProvider,
        "ollama": OllamaProvider,
    }
    
    if provider not in providers:
        raise ProviderError(f"Unknown LLM provider: {provider}")
    
    return providers[provider]()
