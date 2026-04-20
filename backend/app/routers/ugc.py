from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any

from app.models import (
    BaseResponse, UGCCharacterCreate, UGCScriptCreate,
    Character, Task, TaskStatus
)

router = APIRouter(prefix="/api/ugc", tags=["ugc"])


@router.get("/characters/quota")
async def get_character_quota(request: Request) -> dict[str, Any]:
    return {
        "used": 5,
        "limit": 10,
        "remaining": 5,
    }


@router.post("/characters", response_model=Character)
async def create_ugc_character(request: Request, data: UGCCharacterCreate) -> Character:
    return Character(
        id="ugc_char_new",
        name=data.name,
        slug=data.name.lower().replace(" ", "-"),
        description=data.description,
        personality=data.personality,
        backstory=data.backstory,
        gender=data.gender,
        avatar_url=data.avatar_url,
        greeting=data.greeting,
        system_prompt=data.system_prompt,
        tags=data.tags,
        is_official=False,
        creator_id="user_001",
        created_at=datetime.now(),
    )


@router.get("/characters", response_model=list[Character])
async def list_ugc_characters(request: Request) -> list[Character]:
    return [
        Character(
            id="ugc_char_001",
            name="UGC Character",
            slug="ugc-character",
            description="User created character",
            is_official=False,
            creator_id="user_001",
            created_at=datetime.now(),
        )
    ]


@router.put("/characters/{char_id}", response_model=Character)
async def update_ugc_character(
    request: Request, 
    char_id: str, 
    data: UGCCharacterCreate
) -> Character:
    return Character(
        id=char_id,
        name=data.name,
        slug="updated-ugc-character",
        description=data.description,
        is_official=False,
        creator_id="user_001",
        created_at=datetime.now(),
    )


@router.delete("/characters/{char_id}", response_model=BaseResponse)
async def delete_ugc_character(request: Request, char_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="UGC character deleted")


@router.post("/characters/{char_id}/publish", response_model=BaseResponse)
async def publish_ugc_character(request: Request, char_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="UGC character published")


@router.post("/characters/{char_id}/fork", response_model=Character)
async def fork_ugc_character(request: Request, char_id: str) -> Character:
    return Character(
        id="ugc_char_fork",
        name="Forked Character",
        slug="forked-character",
        description="Forked from another character",
        is_official=False,
        creator_id="user_002",
        created_at=datetime.now(),
    )


@router.get("/community/characters", response_model=list[Character])
async def list_community_characters(request: Request) -> list[Character]:
    return [
        Character(
            id="community_char_001",
            name="Community Character",
            slug="community-character",
            description="Community created character",
            is_official=False,
            is_public=True,
            creator_id="creator_001",
            created_at=datetime.now(),
        )
    ]


@router.get("/scripts/quota")
async def get_script_quota(request: Request) -> dict[str, Any]:
    return {
        "used": 3,
        "limit": 5,
        "remaining": 2,
    }


@router.get("/scripts/templates")
async def get_script_templates(request: Request) -> list[dict[str, Any]]:
    return [
        {"id": "template_001", "name": "Romance Script", "description": "A romantic story template"},
        {"id": "template_002", "name": "Adventure Script", "description": "An adventure story template"},
    ]


@router.post("/scripts/from-template", response_model=Task)
async def create_script_from_template(
    request: Request, 
    data: dict[str, Any]
) -> Task:
    return Task(
        id="task_script_template",
        type="script_creation",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/scripts/custom", response_model=BaseResponse)
async def create_custom_script(request: Request, data: UGCScriptCreate) -> BaseResponse:
    return BaseResponse(success=True, message="Custom script created")


@router.put("/scripts/{script_id}", response_model=BaseResponse)
async def update_ugc_script(
    request: Request, 
    script_id: str, 
    data: UGCScriptCreate
) -> BaseResponse:
    return BaseResponse(success=True, message="Script updated")


@router.delete("/scripts/{script_id}", response_model=BaseResponse)
async def delete_ugc_script(request: Request, script_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Script deleted")


@router.post("/scripts/{script_id}/publish", response_model=BaseResponse)
async def publish_ugc_script(request: Request, script_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Script published")


@router.get("/community/scripts")
async def list_community_scripts(request: Request) -> list[dict[str, Any]]:
    return [
        {
            "id": "script_001",
            "title": "Community Script",
            "description": "A community created script",
            "creator_id": "creator_001",
        }
    ]


@router.get("/creator/overview")
async def get_creator_overview(request: Request) -> dict[str, Any]:
    return {
        "creator_id": "creator_001",
        "stats": {
            "total_characters": 10,
            "total_scripts": 5,
            "total_views": 1000,
            "total_favorites": 100,
        },
        "recent_creations": [],
    }
