from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any
from sse_starlette.sse import EventSourceResponse

from app.models import BaseResponse, Task, TaskStatus

router = APIRouter(prefix="/api/novita", tags=["gateway"])


@router.post("/chat/completions")
async def chat_completions(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "completion_001",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello! How can I help you?"},
                "finish_reason": "stop",
            }
        ],
    }


@router.post("/chat/character")
async def chat_character(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "char_chat_001",
        "character_id": data.get("character_id"),
        "response": "Character response",
        "created_at": datetime.now().isoformat(),
    }


@router.post("/images/hunyuan", response_model=Task)
async def generate_hunyuan_image(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_hunyuan",
        type="hunyuan_image",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.get("/task-result/{task_id}")
async def get_task_result(request: Request, task_id: str) -> dict[str, Any]:
    return {
        "task_id": task_id,
        "status": "completed",
        "result": {"image_url": "https://example.com/result.png"},
    }


@router.post("/images/hunyuan/wait")
async def generate_hunyuan_wait(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "image_url": "https://example.com/hunyuan_wait.png",
        "status": "completed",
    }


router_advanced = APIRouter(prefix="/api/novita-advanced", tags=["gateway-advanced"])


@router_advanced.post("/chat/completions")
async def advanced_completions(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "adv_completion_001",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Advanced response"},
                "finish_reason": "stop",
            }
        ],
    }


@router_advanced.post("/chat/stream")
async def advanced_stream(request: Request, data: dict[str, Any]) -> EventSourceResponse:
    async def event_generator():
        yield {"event": "message", "data": "Advanced"}
        yield {"event": "message", "data": " streaming"}
        yield {"event": "done", "data": "[DONE]"}
    return EventSourceResponse(event_generator())


@router_advanced.post("/chat/multimodal")
async def advanced_multimodal(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "multimodal_001",
        "response": "Multimodal response",
        "modality": "text+image",
    }


@router_advanced.post("/chat/function-calling")
async def advanced_function_calling(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "func_call_001",
        "function_call": {
            "name": "get_weather",
            "arguments": '{"location": "Taipei"}',
        },
    }
