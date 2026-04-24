from enum import Enum
from typing import Optional, Any
from datetime import datetime
from pydantic import BaseModel


class EventType(str, Enum):
    MESSAGE_STARTED = "message_started"
    TEXT_DELTA = "text_delta"
    TEXT_DONE = "text_done"
    THINKING_DELTA = "thinking_delta"
    THINKING_DONE = "thinking_done"
    TASK_PENDING = "task_pending"
    TASK_PROGRESS = "task_progress"
    TASK_DONE = "task_done"
    TASK_FAILED = "task_failed"
    ASSET_READY = "asset_ready"
    IMAGE_GENERATING = "image_generating"
    IMAGE_DONE = "image_done"
    VIDEO_SUBMITTED = "video_submitted"
    VIDEO_DONE = "video_done"
    VIDEO_INTENT_DECLINED = "video_intent_declined"
    VOICE_NOTE_PENDING = "voice_note_pending"
    VOICE_NOTE_READY = "voice_note_ready"
    VOICE_NOTE_FAILED = "voice_note_failed"
    CREDIT_UPDATE = "credit_update"
    SESSION_CREATED = "session_created"
    USER_MESSAGE = "user_message"
    STREAM_END = "stream_end"
    ERROR = "error"
    INTIMACY_UPDATED = "intimacy_updated"
    RELATIONSHIP_UPDATE = "relationship_update"
    SCRIPT_STATE_UPDATED = "script_state_updated"
    STORY_COMPLETED = "story_completed"


class SSEEvent(BaseModel):
    event: EventType
    data: dict[str, Any]
    timestamp: datetime = datetime.utcnow()
    
    def to_sse(self) -> dict[str, Any]:
        # sse-starlette formats dicts via str(data), which would produce
        # Python-literal single quotes (invalid JSON for frontend JSON.parse).
        # Always send JSON string payload for SSE `data:` lines.
        import json
        return {"event": self.event.value, "data": json.dumps(self.data, ensure_ascii=False)}


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntentType(str, Enum):
    CHAT = "chat"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    TOOL = "tool"
    SYSTEM = "system"


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    SYSTEM = "system"


class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    VIP = "vip"
