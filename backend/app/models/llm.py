from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    name: Optional[str] = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1)
    stream: bool = False
    user_id: Optional[str] = None
    character_id: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class ChatResponse(BaseModel):
    id: str
    content: str
    model: str
    usage: dict[str, int]
    created: datetime = Field(default_factory=datetime.utcnow)


class IntentType(str, Enum):
    CHAT = "chat"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    VOICE_GENERATION = "voice_generation"
    MEMORY_QUERY = "memory_query"
    MEMORY_UPDATE = "memory_update"
    SYSTEM_COMMAND = "system_command"


class IntentRecognitionResult(BaseModel):
    intent: IntentType
    confidence: float
    entities: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class StructuredOutput(BaseModel):
    action: str
    parameters: dict[str, Any]
    reasoning: Optional[str] = None


class PromptBlock(BaseModel):
    name: str
    content: str
    priority: int = 0
    required: bool = True


class PromptTemplate(BaseModel):
    id: str
    name: str
    blocks: list[PromptBlock]
    version: str = "1.0"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderType(str, Enum):
    NOVITA = "novita"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    OLLAMA = "ollama"
    CLOUDFLARE = "cloudflare"
    LOCAL = "local"


class ModelConfig(BaseModel):
    provider: ProviderType
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 120
