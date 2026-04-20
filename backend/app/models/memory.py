from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class MemoryLayer(str, Enum):
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"


class GlobalMemoryCategory(str, Enum):
    PREFERENCE = "preference"
    FACT = "fact"
    DISLIKE = "dislike"
    INTEREST = "interest"
    RELATIONSHIP = "relationship"


class Memory(BaseModel):
    id: str
    user_id: str
    character_id: str
    content: str
    layer: MemoryLayer = MemoryLayer.EPISODIC
    embedding: Optional[list[float]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    importance: int = Field(default=5, ge=1, le=10)
    decayed_importance: float = Field(default=5.0)
    last_accessed: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class GlobalMemory(BaseModel):
    id: str
    user_id: str
    content: str
    category: GlobalMemoryCategory = GlobalMemoryCategory.PREFERENCE
    source_character_id: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reference_count: int = Field(default=1, ge=0)
    is_confirmed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: datetime = Field(default_factory=datetime.utcnow)


class MemoryCreate(BaseModel):
    user_id: str
    character_id: str
    content: str
    layer: MemoryLayer = MemoryLayer.EPISODIC
    importance: int = Field(default=5, ge=1, le=10)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GlobalMemoryCreate(BaseModel):
    content: str
    category: GlobalMemoryCategory = GlobalMemoryCategory.PREFERENCE
    source_character_id: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class GlobalMemoryPromoteRequest(BaseModel):
    memory_id: str
    category: GlobalMemoryCategory = GlobalMemoryCategory.PREFERENCE


class MemoryQuery(BaseModel):
    user_id: str
    character_id: str
    query: str
    layer: Optional[MemoryLayer] = None
    limit: int = Field(default=10, ge=1, le=100)


class MemoryQueryResult(BaseModel):
    memories: list[Memory]
    total: int
    query: str


class ContextSummary(BaseModel):
    character_id: str
    user_id: str
    working_memory: list[Memory]
    episodic_summary: Optional[str] = None
    semantic_facts: list[str] = Field(default_factory=list)
    global_memories: list[GlobalMemory] = Field(default_factory=list)
    last_interaction: Optional[datetime] = None


class MemoryForgetRequest(BaseModel):
    memory_ids: list[str]


class MemoryCorrectRequest(BaseModel):
    memory_id: str
    new_content: str


class MemoryDecayConfig(BaseModel):
    decay_rate: float = Field(default=0.05, description="Daily decay rate (0.05 = 14-day half-life)")
    decay_threshold: float = Field(default=1.0, description="Minimum importance to keep in active memory")
    importance_min: int = Field(default=1)
    importance_max: int = Field(default=10)


class GlobalMemorySuggestion(BaseModel):
    content: str
    category: GlobalMemoryCategory
    source_character_id: str
    occurrence_count: int
    suggested_confidence: float
