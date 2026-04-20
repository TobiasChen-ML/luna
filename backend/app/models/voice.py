from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class VoiceProvider(str, Enum):
    ELEVENLABS = "elevenlabs"
    DASHSCOPE = "dashscope"
    LIVEKIT = "livekit"


class TTSRequest(BaseModel):
    text: str
    voice_id: Optional[str] = None
    model_id: Optional[str] = None
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0, ge=-12, le=12)
    provider: VoiceProvider = VoiceProvider.ELEVENLABS
    character_id: Optional[str] = None
    user_id: Optional[str] = None
    output_format: str = "mp3"


class TTSResponse(BaseModel):
    audio_url: str
    duration: float
    voice_id: str
    provider: VoiceProvider


class VoiceToken(BaseModel):
    token: str
    expires_at: datetime
    session_id: str


class VoiceConfig(BaseModel):
    provider: VoiceProvider
    voice_id: str
    model_id: Optional[str] = None
    settings: dict[str, Any] = Field(default_factory=dict)


class VoiceNoteRequest(BaseModel):
    message_id: str
    character_id: str
    text: str
    voice_id: Optional[str] = None
