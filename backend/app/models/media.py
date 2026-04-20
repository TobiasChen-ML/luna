from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class ImageGenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    width: int = Field(default=512, ge=64, le=2048)
    height: int = Field(default=512, ge=64, le=2048)
    steps: int = Field(default=20, ge=1, le=100)
    cfg_scale: float = Field(default=7.0, ge=1, le=30)
    seed: Optional[int] = None
    model: Optional[str] = None
    provider: str = "novita"
    character_id: Optional[str] = None
    user_id: Optional[str] = None


class ImageEditRequest(BaseModel):
    image_url: str
    prompt: str
    mask_url: Optional[str] = None
    strength: float = Field(default=0.8, ge=0, le=1)
    provider: str = "novita"


class VideoGenerationRequest(BaseModel):
    prompt: Optional[str] = None
    image_url: Optional[str] = None
    duration: int = Field(default=4, ge=1, le=60)
    fps: int = Field(default=24, ge=1, le=60)
    model: Optional[str] = None
    provider: str = "novita"
    character_id: Optional[str] = None
    user_id: Optional[str] = None


class MediaAsset(BaseModel):
    id: str
    user_id: str
    task_id: Optional[str] = None
    type: MediaType
    url: str
    thumbnail_url: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProviderCallback(BaseModel):
    task_id: str
    status: str
    result_url: Optional[str] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
