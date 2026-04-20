from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    VOICE_NOTE = "voice_note"


class MessageStatus(str, Enum):
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


def generate_session_id() -> str:
    return f"session_{uuid.uuid4().hex[:12]}"


def generate_message_id() -> str:
    return f"msg_{uuid.uuid4().hex[:12]}"


class ChatSessionBase(BaseModel):
    character_id: str
    script_id: Optional[str] = None
    title: Optional[str] = None
    context: Optional[dict[str, Any]] = None


class ChatSessionCreate(ChatSessionBase):
    user_id: str


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    context: Optional[dict[str, Any]] = None
    script_id: Optional[str] = None
    script_state: Optional[str] = None
    script_node_id: Optional[str] = None
    quest_progress: Optional[float] = None


class ChatSession(ChatSessionBase):
    id: str
    user_id: str
    script_state: Optional[str] = None
    script_node_id: Optional[str] = None
    quest_progress: float = 0.0
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatMessageBase(BaseModel):
    content: str
    message_type: MessageType = MessageType.TEXT


class ChatMessageCreate(ChatMessageBase):
    session_id: str
    role: str
    character_id: str
    user_id: str
    audio_url: Optional[str] = None
    image_urls: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class ChatMessage(ChatMessageBase):
    id: str
    session_id: str
    role: str
    character_id: str
    user_id: str
    audio_url: Optional[str] = None
    image_urls: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessage]
    has_more: bool
    oldest_message_id: Optional[str] = None
    total_count: int


class ConversationContext(BaseModel):
    session: Optional[ChatSession] = None
    recent_messages: list[ChatMessage] = Field(default_factory=list)
    character_id: str
    user_id: str
