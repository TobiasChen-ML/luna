from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum
import uuid


class ScriptStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ScriptNodeType(str, Enum):
    SCENE = "scene"
    CHOICE = "choice"
    EVENT = "event"
    ENDING = "ending"


class ScriptState(str, Enum):
    START = "Start"
    BUILD = "Build"
    CLIMAX = "Climax"
    RESOLVE = "Resolve"


def generate_script_id() -> str:
    return f"script_{uuid.uuid4().hex[:12]}"


def generate_node_id() -> str:
    return f"node_{uuid.uuid4().hex[:12]}"


class ScriptNodeBase(BaseModel):
    node_type: ScriptNodeType
    title: Optional[str] = None
    description: Optional[str] = None
    narrative: Optional[str] = None
    character_inner_state: Optional[str] = None
    choices: Optional[list[dict[str, Any]]] = None
    effects: Optional[dict[str, Any]] = None
    triggers: Optional[list[dict[str, Any]]] = None
    media_cue: Optional[dict[str, Any]] = None
    prerequisites: Optional[dict[str, Any]] = None
    emotion_gate: Optional[dict[str, Any]] = None


class ScriptNodeCreate(ScriptNodeBase):
    script_id: str


class ScriptNodeUpdate(BaseModel):
    node_type: Optional[ScriptNodeType] = None
    title: Optional[str] = None
    description: Optional[str] = None
    narrative: Optional[str] = None
    character_inner_state: Optional[str] = None
    choices: Optional[list[dict[str, Any]]] = None
    effects: Optional[dict[str, Any]] = None
    triggers: Optional[list[dict[str, Any]]] = None
    media_cue: Optional[dict[str, Any]] = None
    prerequisites: Optional[dict[str, Any]] = None
    emotion_gate: Optional[dict[str, Any]] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None


class ScriptNode(ScriptNodeBase):
    id: str
    script_id: str
    position_x: int = 0
    position_y: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ScriptBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=250)
    genre: Optional[str] = None
    world_setting: Optional[str] = None
    world_rules: Optional[list[str]] = None
    character_role: Optional[str] = None
    character_setting: Optional[dict[str, Any]] = None
    user_role: Optional[str] = None
    user_role_description: Optional[str] = None
    opening_scene: Optional[str] = None
    opening_line: Optional[str] = None
    emotion_gates: Optional[dict[str, Any]] = None
    triggers: Optional[list[dict[str, Any]]] = None
    tags: Optional[list[str]] = None
    difficulty: str = "normal"
    estimated_duration: Optional[int] = None


class ScriptCreate(ScriptBase):
    character_id: str
    start_node_id: Optional[str] = None


class ScriptUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, max_length=250)
    genre: Optional[str] = None
    world_setting: Optional[str] = None
    world_rules: Optional[list[str]] = None
    character_role: Optional[str] = None
    character_setting: Optional[dict[str, Any]] = None
    user_role: Optional[str] = None
    user_role_description: Optional[str] = None
    opening_scene: Optional[str] = None
    opening_line: Optional[str] = None
    start_node_id: Optional[str] = None
    emotion_gates: Optional[dict[str, Any]] = None
    triggers: Optional[list[dict[str, Any]]] = None
    tags: Optional[list[str]] = None
    difficulty: Optional[str] = None
    estimated_duration: Optional[int] = None
    is_public: Optional[bool] = None
    status: Optional[ScriptStatus] = None


class Script(ScriptBase):
    id: str
    character_id: str
    start_node_id: Optional[str] = None
    play_count: int = 0
    is_public: bool = True
    is_official: bool = False
    status: ScriptStatus = ScriptStatus.DRAFT
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScriptSessionState(BaseModel):
    script_id: str
    session_id: str
    current_node_id: Optional[str] = None
    state: ScriptState = ScriptState.START
    quest_progress: float = 0.0
    variables: dict[str, Any] = Field(default_factory=dict)
    visited_nodes: list[str] = Field(default_factory=list)


class ReviewAction(str, Enum):
    SUBMIT = "submit"
    APPROVE = "approve"
    REJECT = "reject"
    ARCHIVE = "archive"


class ScriptReviewBase(BaseModel):
    script_id: str
    action: ReviewAction
    comment: Optional[str] = None


class ScriptReviewCreate(ScriptReviewBase):
    pass


class ScriptReview(ScriptReviewBase):
    id: str
    reviewer_id: str
    previous_status: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PlayHistoryEntry(BaseModel):
    play_id: str
    play_index: int
    status: str
    ending_type: Optional[str] = None
    completion_time_minutes: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    choices_count: int = 0
