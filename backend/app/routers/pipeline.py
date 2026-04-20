from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any
from sse_starlette.sse import EventSourceResponse

from app.models import BaseResponse, Task, TaskStatus

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.get("/events/user")
async def get_user_events(request: Request) -> EventSourceResponse:
    async def event_generator():
        yield {"event": "connected", "data": "Connected to user event stream"}
    return EventSourceResponse(event_generator())


@router.get("/events/session/{session_id}")
async def get_session_events(request: Request, session_id: str) -> EventSourceResponse:
    async def event_generator():
        yield {"event": "connected", "data": f"Connected to session {session_id}"}
    return EventSourceResponse(event_generator())


@router.post("/generate/audio", response_model=Task)
async def generate_audio(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_audio_gen",
        type="audio_generation",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/generate/multimodal", response_model=Task)
async def generate_multimodal(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_multimodal",
        type="multimodal_generation",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/internal/publish", response_model=BaseResponse)
async def internal_publish(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Content published internally")
