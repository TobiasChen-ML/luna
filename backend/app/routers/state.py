from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any

from app.models import (
    BaseResponse, MemoryCorrectRequest, MemoryForgetRequest,
    RelationshipConsentRequest
)

router = APIRouter(prefix="/api", tags=["state"])


@router.post("/relationship/{character_id}/consent", response_model=BaseResponse)
async def set_relationship_consent(
    request: Request, 
    character_id: str, 
    data: RelationshipConsentRequest
) -> BaseResponse:
    return BaseResponse(success=True, message="Consent updated")


@router.get("/relationship/{character_id}")
async def get_relationship(request: Request, character_id: str) -> dict[str, Any]:
    return {
        "character_id": character_id,
        "level": 5,
        "affection": 0.8,
        "trust": 0.9,
        "status": "dating",
        "created_at": datetime.now().isoformat(),
    }


@router.get("/relationship/{character_id}/visual-permissions")
async def get_visual_permissions(
    request: Request, 
    character_id: str
) -> dict[str, Any]:
    return {
        "character_id": character_id,
        "permissions": {
            "view_gallery": True,
            "view_private_images": False,
            "generate_images": True,
        }
    }


@router.get("/context/{character_id}")
async def get_context(request: Request, character_id: str) -> dict[str, Any]:
    return {
        "character_id": character_id,
        "context": {
            "relationship_stage": "dating",
            "shared_memories": ["memory_001", "memory_002"],
            "recent_topics": ["hobbies", "work"],
        },
        "last_updated": datetime.now().isoformat(),
    }


@router.get("/context/{character_id}/memory")
async def get_context_memory(request: Request, character_id: str) -> dict[str, Any]:
    return {
        "character_id": character_id,
        "memories": [
            {
                "id": "mem_001",
                "content": "User likes coffee",
                "importance": 0.8,
                "created_at": datetime.now().isoformat(),
            }
        ],
        "total": 1,
    }


@router.post("/context/{character_id}/memory/forget", response_model=BaseResponse)
async def forget_memory(
    request: Request, 
    character_id: str, 
    data: MemoryForgetRequest
) -> BaseResponse:
    return BaseResponse(success=True, message=f"Forgot {len(data.memory_ids)} memories")


@router.post("/context/{character_id}/memory/correct", response_model=BaseResponse)
async def correct_memory(
    request: Request, 
    character_id: str, 
    data: MemoryCorrectRequest
) -> BaseResponse:
    return BaseResponse(success=True, message="Memory corrected")
