from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    MESSAGE = "message"
    TASK_UPDATE = "task_update"
    NOTIFICATION = "notification"
    SYSTEM = "system"


class SSEEvent(BaseModel):
    event: EventType
    data: dict[str, Any]
    id: Optional[str] = None
    retry: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PushSubscription(BaseModel):
    user_id: str
    endpoint: str
    keys: dict[str, str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Notification(BaseModel):
    id: str
    user_id: str
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotificationCreate(BaseModel):
    user_id: str
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)


class EventMessage(BaseModel):
    channel: str
    event_type: str
    payload: dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
