from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class APIKeyModel(Base):
    __tablename__ = "api_keys"
    
    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_hash = Column(String(128), nullable=False, unique=True)
    is_active = Column(Integer, default=1)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked_at = Column(DateTime, nullable=True)


class BatchJobModel(Base):
    __tablename__ = "batch_jobs"
    
    id = Column(String(64), primary_key=True)
    user_id = Column(String(64), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    total = Column(Integer, default=0)
    completed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    config = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class APIKey(BaseModel):
    id: str
    user_id: str
    name: str
    key_prefix: str
    key_hash: str
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    revoked_at: Optional[datetime] = None


class APIKeyCreate(BaseModel):
    name: str
    expires_in_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    id: str
    name: str
    key: str
    key_prefix: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class BatchJobType(str, Enum):
    IMAGE_GENERATION = "image_generation"
    SEO_GENERATION = "seo_generation"
    CHARACTER_CREATION = "character_creation"


class BatchJob(BaseModel):
    id: str
    user_id: str
    type: BatchJobType
    status: str = "pending"
    total: int = 0
    completed: int = 0
    failed: int = 0
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BatchJobCreate(BaseModel):
    type: BatchJobType
    config: dict[str, Any]
    items: list[dict[str, Any]]


class SEOKeyword(BaseModel):
    id: str
    keyword: str
    category: Optional[str] = None
    difficulty: Optional[int] = None
    volume: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SEOGenerateRequest(BaseModel):
    template_type: str
    keywords: list[str]
    character_id: Optional[str] = None
