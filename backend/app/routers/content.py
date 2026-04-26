from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any

from app.models import (
    BaseResponse, Character, CharacterCreate, CharacterUpdate, Story, StoryCreate,
    Task, TaskStatus
)

router = APIRouter(prefix="/api/v1", tags=["content"])


@router.post("/characters/import", response_model=Character)
async def import_character(request: Request, data: dict[str, Any]) -> Character:
    return Character(
        id="char_imported",
        name=data.get("name", "Imported Character"),
        slug=data.get("slug", "imported"),
        description=data.get("description"),
        created_at=datetime.now(),
    )


@router.post("/characters/expand", response_model=Character)
async def expand_character(request: Request, data: dict[str, Any]) -> Character:
    return Character(
        id="char_expanded",
        name=data.get("name", "Expanded Character"),
        slug="expanded",
        description="Expanded from base",
        created_at=datetime.now(),
    )


@router.get("/characters", response_model=list[Character])
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


@router.post("/characters", response_model=Character)
async def create_character(request: Request, data: CharacterCreate) -> Character:
    return Character(
        id="char_new",
        name=data.name,
        slug=data.slug,
        description=data.description,
        created_at=datetime.now(),
    )


@router.get("/characters/{character_id}/export")
async def export_character(request: Request, character_id: str) -> dict[str, Any]:
    return {"id": character_id, "name": "Character", "format": "json"}


@router.get("/characters/{character_id}/render-prompt")
async def render_prompt(request: Request, character_id: str) -> dict[str, Any]:
    return {
        "character_id": character_id,
        "system_prompt": "You are a helpful assistant.",
        "rendered_at": datetime.now().isoformat(),
    }


@router.get("/characters/{family_id}/versions")
async def get_character_versions(request: Request, family_id: str) -> list[Character]:
    return [
        Character(
            id=f"{family_id}_v1",
            name="Character v1",
            slug="character-v1",
            family_id=family_id,
            created_at=datetime.now(),
        )
    ]


@router.post("/characters/{character_id}/voice", response_model=Task)
async def set_character_voice(
    request: Request, 
    character_id: str, 
    data: dict[str, Any]
) -> Task:
    return Task(
        id="task_voice",
        type="voice_setup",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.patch("/characters/{character_id}/lifecycle", response_model=BaseResponse)
async def update_lifecycle(
    request: Request, 
    character_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    return BaseResponse(success=True, message="Lifecycle updated")


@router.get("/characters/{character_id}", response_model=Character)
async def get_character(request: Request, character_id: str) -> Character:
    return Character(
        id=character_id,
        name="Character",
        slug="character",
        description="A character",
        created_at=datetime.now(),
    )


@router.put("/characters/{character_id}", response_model=Character)
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


@router.delete("/characters/{character_id}", response_model=BaseResponse)
async def delete_character(request: Request, character_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Character deleted")


@router.post("/stories", response_model=Story)
async def create_story(request: Request, data: StoryCreate) -> Story:
    return Story(
        id="story_new",
        title=data.title,
        slug=data.slug,
        description=data.description,
        character_id=data.character_id,
        nodes=data.nodes,
        created_at=datetime.now(),
    )


@router.get("/stories", response_model=list[Story])
async def get_stories(request: Request) -> list[Story]:
    return [
        Story(
            id="story_001",
            title="Story One",
            slug="story-one",
            character_id="char_001",
            created_at=datetime.now(),
        )
    ]


@router.get("/stories/{story_id}", response_model=Story)
async def get_story(request: Request, story_id: str) -> Story:
    return Story(
        id=story_id,
        title="Story",
        slug="story",
        character_id="char_001",
        created_at=datetime.now(),
    )


@router.get("/stories/{story_id}/characters")
async def get_story_characters(request: Request, story_id: str) -> list[Character]:
    return [
        Character(
            id="char_001",
            name="Story Character",
            slug="story-character",
            created_at=datetime.now(),
        )
    ]


@router.post("/stories/{story_id}/characters/{character_id}", response_model=BaseResponse)
async def add_story_character(
    request: Request, 
    story_id: str, 
    character_id: str
) -> BaseResponse:
    return BaseResponse(success=True, message="Character added to story")


@router.delete("/stories/{story_id}/characters/{character_id}", response_model=BaseResponse)
async def remove_story_character(
    request: Request, 
    story_id: str, 
    character_id: str
) -> BaseResponse:
    return BaseResponse(success=True, message="Character removed from story")


@router.post("/stories/async", response_model=Task)
async def create_story_async(request: Request, data: StoryCreate) -> Task:
    return Task(
        id="task_story",
        type="story_creation",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/memory/index", response_model=BaseResponse)
async def index_memory(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Memory indexed")


@router.post("/memory/query")
async def query_memory(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "results": [
            {"id": "mem_001", "content": "Memory content", "score": 0.95}
        ],
        "total": 1,
    }


@router.post("/memory/extract", response_model=BaseResponse)
async def extract_memory(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Memory extracted")


@router.delete("/memory/index/{memory_id}", response_model=BaseResponse)
async def delete_memory(request: Request, memory_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Memory deleted")


@router.get("/memory/stats")
async def get_memory_stats(request: Request) -> dict[str, Any]:
    return {
        "total_memories": 100,
        "total_size_mb": 50.5,
        "last_indexed": datetime.now().isoformat(),
    }


@router.get("/memory/health")
async def get_memory_health(request: Request) -> dict[str, Any]:
    return {"status": "healthy", "latency_ms": 10}


@router.get("/prompts")
async def get_prompts(request: Request) -> list[dict[str, Any]]:
    return [
        {"name": "default", "description": "Default prompt template"},
        {"name": "creative", "description": "Creative writing prompt"},
    ]


@router.get("/prompts/{name}")
async def get_prompt(request: Request, name: str) -> dict[str, Any]:
    return {
        "name": name,
        "content": "You are a helpful assistant.",
        "description": f"Prompt template: {name}",
    }


@router.put("/prompts/{name}", response_model=BaseResponse)
async def update_prompt(request: Request, name: str, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Prompt updated")


@router.delete("/prompts/{name}", response_model=BaseResponse)
async def delete_prompt(request: Request, name: str) -> BaseResponse:
    return BaseResponse(success=True, message="Prompt deleted")


@router.get("/templates")
async def get_templates(request: Request) -> list[dict[str, Any]]:
    return [
        {"id": "template_001", "name": "Default Template"},
    ]


@router.get("/templates/{template_id}")
async def get_template(request: Request, template_id: str) -> dict[str, Any]:
    return {"id": template_id, "name": "Template", "content": "Template content"}


@router.get("/categories")
async def get_categories(request: Request) -> list[dict[str, Any]]:
    return [
        {"id": "cat_001", "name": "Romance", "slug": "romance"},
    ]


def _collections_deprecated() -> None:
    raise HTTPException(
        status_code=410,
        detail="Legacy /api/v1/collections endpoints are deprecated. Use the v2 collection APIs.",
    )


@router.post("/collections", response_model=BaseResponse)
async def create_collection(request: Request, data: dict[str, Any]) -> BaseResponse:
    _collections_deprecated()


@router.get("/collections")
async def get_collections(request: Request) -> list[dict[str, Any]]:
    _collections_deprecated()


@router.get("/collections/{collection_id}")
async def get_collection(request: Request, collection_id: str) -> dict[str, Any]:
    _collections_deprecated()


@router.put("/collections/{collection_id}", response_model=BaseResponse)
async def update_collection(
    request: Request, 
    collection_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    _collections_deprecated()


@router.delete("/collections/{collection_id}", response_model=BaseResponse)
async def delete_collection(request: Request, collection_id: str) -> BaseResponse:
    _collections_deprecated()


@router.get("/collections/{collection_id}/characters")
async def get_collection_characters(
    request: Request, 
    collection_id: str
) -> list[Character]:
    _collections_deprecated()


@router.post("/collections/{collection_id}/characters/{char_id}", response_model=BaseResponse)
async def add_to_collection(
    request: Request, 
    collection_id: str, 
    char_id: str
) -> BaseResponse:
    _collections_deprecated()


@router.delete("/collections/{collection_id}/characters/{char_id}", response_model=BaseResponse)
async def remove_from_collection(
    request: Request, 
    collection_id: str, 
    char_id: str
) -> BaseResponse:
    _collections_deprecated()


@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(request: Request, task_id: str) -> Task:
    return Task(
        id=task_id,
        type="generic",
        status=TaskStatus.COMPLETED,
        created_at=datetime.now(),
    )


@router.get("/tasks", response_model=list[Task])
async def get_tasks(request: Request) -> list[Task]:
    return [
        Task(
            id="task_001",
            type="generic",
            status=TaskStatus.COMPLETED,
            created_at=datetime.now(),
        )
    ]


@router.post("/voice/tts", response_model=Task)
async def text_to_speech(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_tts",
        type="tts",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/voice/tts/with-presence", response_model=Task)
async def tts_with_presence(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_tts_presence",
        type="tts_with_presence",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.get("/voice/health")
async def get_voice_health(request: Request) -> dict[str, Any]:
    return {"status": "healthy"}
