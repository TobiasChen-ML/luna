from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any

from app.models import (
    BaseResponse, Character, Story, Task, TaskStatus,
    CharacterCreate, CharacterUpdate, StoryCreate, StoryUpdate,
    MemoryCorrectRequest, MemoryForgetRequest, RelationshipConsentRequest
)

router = APIRouter(tags=["world"])


character_router = APIRouter(prefix="/api/world/characters", tags=["world-characters"])


@character_router.get("/official", response_model=list[Character])
async def get_official_characters(request: Request) -> list[Character]:
    return [
        Character(
            id="official_001",
            name="Official Character",
            slug="official-character",
            description="An official character",
            is_official=True,
            created_at=datetime.now(),
        )
    ]


@character_router.get("/official/{character_id}", response_model=Character)
async def get_official_character(request: Request, character_id: str) -> Character:
    return Character(
        id=character_id,
        name="Official Character",
        slug="official-character",
        description="An official character",
        is_official=True,
        created_at=datetime.now(),
    )


@character_router.post("", response_model=Character)
async def create_character(request: Request, data: CharacterCreate) -> Character:
    return Character(
        id="char_new",
        name=data.name,
        slug=data.slug or data.name.lower().replace(" ", "-"),
        description=data.description,
        personality=data.personality_summary,
        backstory=data.backstory,
        gender=data.gender,
        avatar_url=data.avatar_url,
        cover_url=data.cover_url,
        greeting=data.greeting,
        system_prompt=data.system_prompt,
        tags=data.personality_tags or [],
        is_public=data.is_public,
        created_at=datetime.now(),
    )


@character_router.get("/categories")
async def get_categories(request: Request) -> list[dict[str, Any]]:
    return [
        {"id": "cat_001", "name": "Romance", "slug": "romance"},
    ]


@character_router.get("/discover")
async def discover_characters(request: Request) -> list[Character]:
    return [
        Character(
            id="discover_001",
            name="Discoverable",
            slug="discoverable",
            created_at=datetime.now(),
        )
    ]


@character_router.get("/by-slug/{slug}", response_model=Character)
async def get_by_slug(request: Request, slug: str) -> Character:
    return Character(
        id="char_slug",
        name="Character by Slug",
        slug=slug,
        created_at=datetime.now(),
    )


@character_router.get("", response_model=list[Character])
async def get_characters(request: Request) -> list[Character]:
    return [
        Character(
            id="char_001",
            name="Character",
            slug="character",
            description="A character",
            created_at=datetime.now(),
        )
    ]


@character_router.get("/{character_id}", response_model=Character)
async def get_character(request: Request, character_id: str) -> Character:
    return Character(
        id=character_id,
        name="Character",
        slug="character",
        description="A character",
        created_at=datetime.now(),
    )


@character_router.put("/{character_id}", response_model=Character)
async def update_character(
    request: Request, 
    character_id: str, 
    data: CharacterUpdate
) -> Character:
    return Character(
        id=character_id,
        name=data.name or "Updated",
        slug=data.slug or "updated",
        description=data.description,
        created_at=datetime.now(),
    )


@character_router.delete("/{character_id}", response_model=BaseResponse)
async def delete_character(request: Request, character_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Character deleted")


@character_router.post("/{character_id}/lock-relationship", response_model=BaseResponse)
async def lock_relationship(request: Request, character_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Relationship locked")


@character_router.post("/{character_id}/force-routing", response_model=BaseResponse)
async def force_routing(
    request: Request, 
    character_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    return BaseResponse(success=True, message="Force routing applied")


@character_router.get("/force-routing/templates")
async def get_routing_templates(request: Request) -> list[dict[str, Any]]:
    return [{"id": "template_001", "name": "Default Routing"}]


@character_router.get("/{character_id}/export")
async def export_character(request: Request, character_id: str) -> dict[str, Any]:
    return {"id": character_id, "name": "Character", "format": "json"}


@character_router.post("/import", response_model=Character)
async def import_character(request: Request, data: dict[str, Any]) -> Character:
    return Character(
        id="char_imported",
        name=data.get("name", "Imported"),
        slug="imported",
        created_at=datetime.now(),
    )


@character_router.post("/{character_id}/train-lora", response_model=Task)
async def train_lora(request: Request, character_id: str) -> Task:
    return Task(
        id="task_lora",
        type="lora_training",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@character_router.get("/{character_id}/lora-status", response_model=Task)
async def get_lora_status(request: Request, character_id: str) -> Task:
    return Task(
        id="task_lora",
        type="lora_training",
        status=TaskStatus.PROCESSING,
        progress=0.5,
        created_at=datetime.now(),
    )


@character_router.post("/{character_id}/sync-factory", response_model=BaseResponse)
async def sync_factory(request: Request, character_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Synced with factory")


@character_router.post("/voice/preview", response_model=Task)
async def preview_voice(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_voice_preview",
        type="voice_preview",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@character_router.get("/voice/preview/{task_id}", response_model=Task)
async def get_voice_preview(request: Request, task_id: str) -> Task:
    return Task(
        id=task_id,
        type="voice_preview",
        status=TaskStatus.COMPLETED,
        result={"audio_url": "https://example.com/preview.mp3"},
        created_at=datetime.now(),
    )


story_router = APIRouter(prefix="/api/world/stories", tags=["world-stories"])


@story_router.get("/available/{character_id}")
async def get_available_stories(request: Request, character_id: str) -> list[Story]:
    return [
        Story(
            id="story_avail",
            title="Available Story",
            character_id=character_id,
            created_at=datetime.now(),
        )
    ]


@story_router.get("/character/{character_id}")
async def get_character_stories(request: Request, character_id: str) -> list[Story]:
    return [
        Story(
            id="story_char",
            title="Character Story",
            character_id=character_id,
            created_at=datetime.now(),
        )
    ]


@story_router.get("/{story_id}", response_model=Story)
async def get_story(request: Request, story_id: str) -> Story:
    return Story(
        id=story_id,
        title="Story",
        character_id="char_001",
        created_at=datetime.now(),
    )


@story_router.get("/{story_id}/nodes")
async def get_story_nodes(request: Request, story_id: str) -> list[dict[str, Any]]:
    return [{"id": "node_001", "content": "Node content"}]


@story_router.post("/{story_id}/start", response_model=BaseResponse)
async def start_story(request: Request, story_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Story started")


@story_router.post("/{story_id}/resume", response_model=BaseResponse)
async def resume_story(request: Request, story_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Story resumed")


@story_router.post("/{story_id}/choice")
async def make_choice(request: Request, story_id: str, data: dict[str, Any]) -> dict[str, Any]:
    return {"story_id": story_id, "next_node_id": "node_002"}


@story_router.get("/progress/{character_id}")
async def get_progress(request: Request, character_id: str) -> dict[str, Any]:
    return {"character_id": character_id, "progress": 0.5}


@story_router.post("/{story_id}/storyboard/generate", response_model=Task)
async def generate_storyboard(request: Request, story_id: str) -> Task:
    return Task(
        id="task_storyboard",
        type="storyboard",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@story_router.post("", response_model=Story)
async def create_story(request: Request, data: StoryCreate) -> Story:
    return Story(
        id="story_new",
        title=data.title,
        character_id=data.character_id,
        created_at=datetime.now(),
    )


@story_router.put("/{story_id}", response_model=Story)
async def update_story(request: Request, story_id: str, data: StoryUpdate) -> Story:
    return Story(
        id=story_id,
        title=data.title or "Updated",
        character_id="char_001",
        created_at=datetime.now(),
    )


@story_router.delete("/{story_id}", response_model=BaseResponse)
async def delete_story(request: Request, story_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Story deleted")


@story_router.post("/{story_id}/nodes", response_model=BaseResponse)
async def create_node(request: Request, story_id: str, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Node created")


@story_router.put("/nodes/{node_id}", response_model=BaseResponse)
async def update_node(request: Request, node_id: str, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Node updated")


@story_router.delete("/nodes/{node_id}", response_model=BaseResponse)
async def delete_node(request: Request, node_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Node deleted")


@story_router.post("/admin/create", response_model=Story)
async def admin_create(request: Request, data: StoryCreate) -> Story:
    return Story(
        id="story_admin",
        title=data.title,
        character_id=data.character_id,
        created_at=datetime.now(),
    )


@story_router.put("/admin/{story_id}", response_model=Story)
async def admin_update(request: Request, story_id: str, data: StoryUpdate) -> Story:
    return Story(
        id=story_id,
        title=data.title or "Admin Updated",
        character_id="char_001",
        created_at=datetime.now(),
    )


@story_router.delete("/admin/{story_id}", response_model=BaseResponse)
async def admin_delete(request: Request, story_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Story deleted by admin")


context_router = APIRouter(prefix="/api/context", tags=["world-context"])


@context_router.get("/{character_id}")
async def get_context(request: Request, character_id: str) -> dict[str, Any]:
    return {"character_id": character_id, "context": {}}


@context_router.get("/{character_id}/memory")
async def get_memory(request: Request, character_id: str) -> dict[str, Any]:
    return {"character_id": character_id, "memories": []}


@context_router.post("/{character_id}/memory/forget", response_model=BaseResponse)
async def forget_memory(
    request: Request, 
    character_id: str, 
    data: MemoryForgetRequest
) -> BaseResponse:
    return BaseResponse(success=True, message="Memory forgotten")


@context_router.post("/{character_id}/memory/correct", response_model=BaseResponse)
async def correct_memory(
    request: Request, 
    character_id: str, 
    data: MemoryCorrectRequest
) -> BaseResponse:
    return BaseResponse(success=True, message="Memory corrected")


relationship_router = APIRouter(prefix="/api/relationship", tags=["world-relationship"])


@relationship_router.post("/{character_id}/consent", response_model=BaseResponse)
async def set_consent(
    request: Request, 
    character_id: str, 
    data: RelationshipConsentRequest
) -> BaseResponse:
    return BaseResponse(success=True, message="Consent updated")


@relationship_router.get("/{character_id}")
async def get_relationship(request: Request, character_id: str) -> dict[str, Any]:
    return {"character_id": character_id, "level": 5}


@relationship_router.get("/{character_id}/visual-permissions")
async def get_visual_perms(request: Request, character_id: str) -> dict[str, Any]:
    return {"character_id": character_id, "permissions": {}}
