from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator, Any
from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str


class LLMRequest(BaseModel):
    messages: list[Message]
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    stream: bool = False
    response_format: Optional[dict] = None
    tools: Optional[list[dict]] = None


class LLMResponse(BaseModel):
    content: str
    model: str
    usage: dict
    finish_reason: str = "stop"


class StructuredResponse(BaseModel):
    data: dict[str, Any]
    raw_content: str


class BaseLLMProvider(ABC):
    def __init__(self, api_key: str, base_url: str, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        pass
    
    @abstractmethod
    async def generate_stream(self, request: LLMRequest) -> AsyncIterator[str]:
        pass
    
    @abstractmethod
    async def generate_structured(
        self,
        request: LLMRequest,
        schema: dict
    ) -> StructuredResponse:
        pass
    
    async def health_check(self) -> bool:
        try:
            response = await self.generate(LLMRequest(
                messages=[Message(role="user", content="ping")],
                max_tokens=5
            ))
            return bool(response.content)
        except Exception:
            return False
    
    def _build_openai_request(self, request: LLMRequest) -> dict:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        
        body = {
            "model": request.model or self.config.get("default_model"),
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": request.stream,
        }
        
        if request.response_format:
            body["response_format"] = request.response_format
        
        if request.tools:
            body["tools"] = request.tools
        
        return body