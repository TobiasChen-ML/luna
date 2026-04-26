from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Query, Depends
from typing import Any, Optional
import uuid

from app.models import BaseResponse, Task, TaskStatus
from app.services.character_service import character_service
from app.services.voice_service import VoiceService
from app.core.dependencies import get_current_user_required, get_optional_user
from app.models import User

router = APIRouter(prefix="/api/characters", tags=["characters"])
voice_service = VoiceService()
_voice_preview_tasks: dict[str, Task] = {}

_MATURE_FIELDS = {"mature_image_url", "mature_cover_url", "mature_video_url"}
_VOICE_PREVIEW_ALIASES: dict[str, str] = {
    "ASMR_Whisperer": "j05EIz3iI3JmBTWC3CsA",
    "Sensual_Hypnotic": "PB6BdkFkZLbI39GHdnbQ",
    "Soft_Husky": "6z4qitu552uH4K9c5vrj",
    "Mysterious_Warm": "rsCVCASkcJ6wDNekWF5H",
    "Hollywood_Actress": "MftN0gvsFPPOYnV3DU0Y",
    "Lively_Girl": "JnLbZVB3BDIX9KH4Bc1H",
    "Seductive_Calm": "ZP7ctTmcovXNUmOj695o",
    "Meditative_ASMR": "du9lwz8ZPYY8gsZt7QO5",
}


def _strip_mature(character: dict) -> dict:
    return {k: v for k, v in character.items() if k not in _MATURE_FIELDS}


def _filter_characters(characters: list[dict], authenticated: bool) -> list[dict]:
    if authenticated:
        return characters
    return [_strip_mature(c) for c in characters]


def _resolve_preview_voice_inputs(raw_voice_id: str) -> tuple[str, str]:
    # Keep backwards compatibility: UI may send alias, db id, or provider voice id.
    normalized = (raw_voice_id or "").strip() or "default"
    return _VOICE_PREVIEW_ALIASES.get(normalized, normalized), normalized


@router.get("/official")
async def get_official_characters(
    request: Request,
    top_category: Optional[str] = Query(None),
    limit: int = Query(20),
    offset: int = Query(0),
    user: Optional[User] = Depends(get_optional_user),
) -> list[dict[str, Any]]:
    characters, _ = await character_service.list_official_characters(
        top_category=top_category,
        page=(offset // limit) + 1,
        page_size=limit,
    )
    return _filter_characters(characters, authenticated=user is not None)


@router.get("/official/{character_id}")
async def get_official_character(
    request: Request,
    character_id: str,
    user: Optional[User] = Depends(get_optional_user),
) -> dict[str, Any]:
    character = await character_service.get_character_by_id(character_id)
    if not character:
        character = await character_service.get_character_by_slug(character_id)

    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    if not character.get("is_official"):
        raise HTTPException(status_code=404, detail="Character not found")

    await character_service.increment_view_count(character_id)

    return character


@router.get("/categories")
async def get_categories(request: Request) -> dict[str, Any]:
    categories_raw = await character_service.get_categories_with_counts()
    
    categories = [
        {"id": "girls", "slug": "girls", "name": "Girls", "count": 0, "filter_tags": []},
        {"id": "anime", "slug": "anime", "name": "Anime", "count": 0, "filter_tags": []},
        {"id": "guys", "slug": "guys", "name": "Guys", "count": 0, "filter_tags": []},
    ]
    
    for cat in categories_raw:
        for c in categories:
            if c["slug"] == cat["slug"]:
                c["count"] = cat["count"]
    
    for cat in categories:
        filter_tags = await character_service.get_filter_tags(cat["slug"])
        cat["filter_tags"] = filter_tags
    
    return {"categories": categories}


@router.get("/discover")
async def discover_characters(
    request: Request,
    top_category: str = Query("girls"),
    filter_tag: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    limit: int = Query(24),
    offset: int = Query(0),
    personalized: bool = Query(True),
    user: Optional[User] = Depends(get_optional_user),
) -> list[dict[str, Any]]:
    if personalized and user:
        from app.services.recommender_service import recommender_service
        characters = await recommender_service.get_personalized_discover(
            user_id=user.id,
            top_category=top_category,
            filter_tag=filter_tag,
            search=name,
            limit=limit,
            offset=offset,
        )
        return characters  # authenticated — return full data

    characters = await character_service.discover_characters(
        top_category=top_category,
        filter_tag=filter_tag,
        search=name,
        limit=limit,
        offset=offset,
    )
    return characters


@router.post("/ugc", response_model=dict[str, Any])
async def create_ugc_character(
    request: Request,
    data: dict[str, Any],
    user: User = Depends(get_current_user_required)
) -> dict[str, Any]:
    from app.models.character import CharacterCreate
    
    character_create = CharacterCreate(**data)
    character = await character_service.create_ugc_character(character_create, user.id)
    
    return character


@router.get("/my", response_model=dict[str, Any])
async def list_my_characters(
    request: Request,
    page: int = Query(1),
    page_size: int = Query(20),
    user: User = Depends(get_current_user_required)
) -> dict[str, Any]:
    characters, total = await character_service.list_user_characters(
        user_id=user.id,
        page=page,
        page_size=page_size,
    )
    
    return {
        "items": characters,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/by-slug/{slug}")
async def get_character_by_slug(request: Request, slug: str) -> dict[str, Any]:
    character = await character_service.get_character_by_slug(slug)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    await character_service.increment_view_count(character["id"])
    
    return character


@router.post("/{character_id}/view")
async def record_character_view(
    request: Request,
    character_id: str,
    data: Optional[dict[str, Any]] = None,
    user: User = Depends(get_current_user_required),
) -> dict[str, Any]:
    character = await character_service.get_character_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    from app.services.user_preference_service import user_preference_service
    
    view_duration = 0
    if data:
        view_duration = data.get("view_duration_seconds", 0)
    
    view_id = await user_preference_service.record_view(
        user_id=user.id,
        character_id=character_id,
        view_duration_seconds=view_duration,
    )
    
    return {"success": True, "view_id": view_id}


@router.post("/{character_id}/favorite")
async def add_character_favorite(
    request: Request,
    character_id: str,
    user: User = Depends(get_current_user_required),
) -> dict[str, Any]:
    character = await character_service.get_character_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    from app.services.user_preference_service import user_preference_service
    
    result = await user_preference_service.add_favorite(user_id=user.id, character_id=character_id)
    return result


@router.delete("/{character_id}/favorite")
async def remove_character_favorite(
    request: Request,
    character_id: str,
    user: User = Depends(get_current_user_required),
) -> dict[str, Any]:
    from app.services.user_preference_service import user_preference_service
    
    success = await user_preference_service.remove_favorite(user_id=user.id, character_id=character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Favorite not found")
    
    return {"success": True, "message": "Favorite removed"}


@router.get("/{character_id}/favorite-status")
async def check_favorite_status(
    request: Request,
    character_id: str,
    user: Optional[User] = Depends(get_optional_user),
) -> dict[str, Any]:
    if not user:
        return {"is_favorited": False}
    
    from app.services.user_preference_service import user_preference_service
    
    is_favorited = await user_preference_service.is_favorited(user_id=user.id, character_id=character_id)
    return {"is_favorited": is_favorited}


@router.get("/favorites")
async def list_favorites(
    request: Request,
    page: int = Query(1),
    page_size: int = Query(20),
    user: User = Depends(get_current_user_required),
) -> dict[str, Any]:
    from app.services.user_preference_service import user_preference_service
    
    favorites, total = await user_preference_service.get_favorites(
        user_id=user.id,
        page=page,
        page_size=page_size,
    )
    
    return {
        "items": favorites,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/force-routing/templates")
async def get_routing_templates(request: Request) -> list[dict[str, Any]]:
    return [
        {"id": "template_001", "name": "Default Routing"},
        {"id": "template_002", "name": "Advanced Routing"},
    ]


@router.get("")
async def list_characters(
    request: Request,
    page: int = Query(1),
    page_size: int = Query(20),
    top_category: Optional[str] = Query(None),
    is_official: Optional[bool] = Query(None),
    is_public: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    user: Optional[User] = Depends(get_optional_user),
) -> list[dict[str, Any]]:
    characters, _ = await character_service.list_characters(
        page=page,
        page_size=page_size,
        top_category=top_category,
        is_official=is_official,
        is_public=is_public,
        search=search,
    )
    return _filter_characters(characters, authenticated=user is not None)


@router.post("", response_model=dict[str, Any])
async def create_character(
    request: Request,
    data: dict[str, Any],
    user: User = Depends(get_current_user_required),
) -> dict[str, Any]:
    from app.models.character import CharacterCreate
    
    character_create = CharacterCreate(**data)
    character = await character_service.create_ugc_character(character_create, user.id)
    
    return character


@router.get("/{character_id}")
async def get_character(
    request: Request,
    character_id: str,
    user: Optional[User] = Depends(get_optional_user),
) -> dict[str, Any]:
    character = await character_service.get_character_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character if user else _strip_mature(character)


@router.put("/{character_id}")
async def update_character(
    request: Request, 
    character_id: str, 
    data: dict[str, Any]
) -> dict[str, Any]:
    from app.models.character import CharacterUpdate
    
    update_data = CharacterUpdate(**data)
    character = await character_service.update_character(character_id, update_data)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return character


@router.delete("/{character_id}", response_model=BaseResponse)
async def delete_character(request: Request, character_id: str) -> BaseResponse:
    success = await character_service.delete_character(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return BaseResponse(success=True, message="Character deleted")


@router.post("/import")
async def import_character(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    from app.models.character import CharacterCreate
    
    import_data = {
        "name": data.get("name", "Imported Character"),
        "description": data.get("description"),
        "personality_tags": data.get("tags", []),
        "backstory": data.get("backstory"),
        "avatar_url": data.get("avatar_url"),
        "greeting": data.get("greeting"),
        "system_prompt": data.get("system_prompt"),
    }
    
    character_create = CharacterCreate(**import_data)
    character = await character_service.create_character(character_create)
    
    return character


@router.get("/{character_id}/export")
async def export_character(request: Request, character_id: str) -> dict[str, Any]:
    character = await character_service.get_character_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    export_data = {
        "id": character["id"],
        "name": character["name"],
        "slug": character["slug"],
        "description": character.get("description"),
        "personality_tags": character.get("personality_tags", []),
        "backstory": character.get("backstory"),
        "avatar_url": character.get("avatar_url"),
        "greeting": character.get("greeting"),
        "system_prompt": character.get("system_prompt"),
        "format": "json",
    }
    
    return export_data


@router.post("/{character_id}/sync-factory", response_model=BaseResponse)
async def sync_factory(request: Request, character_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Character synced with factory")


@router.post("/{character_id}/force-routing", response_model=BaseResponse)
async def force_routing(
    request: Request, 
    character_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    return BaseResponse(success=True, message="Force routing applied")


@router.post("/{character_id}/train-lora", response_model=Task)
async def train_lora(request: Request, character_id: str) -> Task:
    return Task(
        id="task_lora_001",
        type="lora_training",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.get("/{character_id}/lora-status", response_model=Task)
async def get_lora_status(request: Request, character_id: str) -> Task:
    return Task(
        id="task_lora_001",
        type="lora_training",
        status=TaskStatus.PROCESSING,
        progress=0.5,
        created_at=datetime.now(),
    )


@router.post("/{character_id}/lock-relationship", response_model=BaseResponse)
async def lock_relationship(request: Request, character_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Relationship locked")


@router.post("/voice/preview", response_model=Task)
async def preview_voice(
    request: Request,
    data: Optional[dict[str, Any]] = None,
    voice_id: Optional[str] = Query(None),
) -> Task:
    payload = data or {}
    requested_voice_id = str(payload.get("voice_id") or voice_id or "default")
    preview_voice_id, preview_voice_db_id = _resolve_preview_voice_inputs(requested_voice_id)

    preview_text = payload.get("text") or "Hello, this is your voice preview."
    task_id = f"task_voice_preview_{uuid.uuid4().hex[:8]}"

    task = Task(
        id=task_id,
        type="voice_preview",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )
    _voice_preview_tasks[task_id] = task

    try:
        result = await voice_service.generate_tts(
            text=preview_text,
            voice_id=preview_voice_id,
            voice_db_id=preview_voice_db_id,
        )
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.progress = 1.0
    except Exception as exc:
        task.status = TaskStatus.FAILED
        task.error = str(exc)
    finally:
        task.updated_at = datetime.now()

    _voice_preview_tasks[task_id] = task
    return task


@router.get("/voice/preview/{task_id}", response_model=Task)
async def get_voice_preview(request: Request, task_id: str) -> Task:
    task = _voice_preview_tasks.get(task_id)
    if not task and task_id == "task_voice_preview" and _voice_preview_tasks:
        # Backward compatibility for older clients hard-coding this task id.
        task = next(reversed(_voice_preview_tasks.values()))
    if not task:
        task = Task(
            id=task_id,
            type="voice_preview",
            status=TaskStatus.FAILED,
            error="Voice preview task not found",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    return task
