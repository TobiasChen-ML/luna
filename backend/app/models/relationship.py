from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class RelationshipStage(str, Enum):
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE = "close"
    INTIMATE = "intimate"
    SOULMATE = "soulmate"


class RelationshipBase(BaseModel):
    intimacy: float = Field(default=0, ge=0, le=100)
    trust: float = Field(default=0, ge=0, le=100)
    desire: float = Field(default=0, ge=0, le=100)
    dependency: float = Field(default=0, ge=0, le=100)
    stage: RelationshipStage = RelationshipStage.STRANGER


class RelationshipCreate(RelationshipBase):
    user_id: str
    character_id: str
    script_id: Optional[str] = None


class RelationshipUpdate(BaseModel):
    intimacy: Optional[float] = Field(None, ge=0, le=100)
    trust: Optional[float] = Field(None, ge=0, le=100)
    desire: Optional[float] = Field(None, ge=0, le=100)
    dependency: Optional[float] = Field(None, ge=0, le=100)
    stage: Optional[RelationshipStage] = None
    history_summary: Optional[str] = None
    is_locked: Optional[bool] = None


class Relationship(RelationshipBase):
    id: str
    user_id: str
    character_id: str
    script_id: Optional[str] = None
    is_locked: bool = False
    locked_at: Optional[datetime] = None
    history_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RelationshipAnalysisResult(BaseModel):
    sentiment: str = "neutral"
    intimacy_change: float = 0
    trust_change: float = 0
    desire_change: float = 0
    dependency_change: float = 0
    stage_transition: Optional[str] = None
    reasoning: str = ""


class RelationshipUpdateEvent(BaseModel):
    character_id: str
    intimacy: float
    trust: float
    desire: float
    dependency: float
    stage: str
    previous_stage: Optional[str] = None
    change_summary: Optional[str] = None
