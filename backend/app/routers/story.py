from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any, Optional
import uuid
import json

from app.models import (
    BaseResponse, Story, StoryCreate, StoryUpdate, Task, TaskStatus, StoryStatus
)
from app.services.choice_matcher import choice_matcher
from app.services.story_service import story_service
from app.core.database import db

router = APIRouter(prefix="/api/stories", tags=["stories"])


@router.get("/available/{character_id}")
async def get_available_stories(request: Request, character_id: str) -> list[Story]:
    return [
        Story(
            id="story_avail_001",
            title="Available Story",
            slug="available-story",
            character_id=character_id,
            status=StoryStatus.PUBLISHED,
            created_at=datetime.now(),
        )
    ]


@router.get("/character/{character_id}")
async def get_character_stories(request: Request, character_id: str) -> list[Story]:
    return [
        Story(
            id="story_char_001",
            title="Character Story",
            slug="character-story",
            character_id=character_id,
            created_at=datetime.now(),
        )
    ]


@router.get("/{story_id}", response_model=Story)
async def get_story(request: Request, story_id: str) -> Story:
    return Story(
        id=story_id,
        title="Story",
        slug="story",
        character_id="char_001",
        created_at=datetime.now(),
    )


@router.get("/{story_id}/nodes")
async def get_story_nodes(request: Request, story_id: str) -> list[dict[str, Any]]:
    return [
        {
            "id": "node_001",
            "story_id": story_id,
            "content": "Story node content",
            "choices": [{"text": "Choice A", "next_node_id": "node_002"}],
        }
    ]


@router.post("/{story_id}/start", response_model=BaseResponse)
async def start_story(request: Request, story_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Story started")


@router.post("/{story_id}/resume", response_model=BaseResponse)
async def resume_story(request: Request, story_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Story resumed")


@router.post("/{story_id}/choice")
async def make_story_choice(
    request: Request, 
    story_id: str, 
    data: dict[str, Any]
) -> dict[str, Any]:
    return {
        "story_id": story_id,
        "next_node_id": "node_002",
        "content": "Next story content",
        "choices": [],
    }


@router.post("/{story_id}/match-choice")
async def match_user_choice(
    request: Request,
    story_id: str,
    data: dict[str, Any]
) -> dict[str, Any]:
    user_message = data.get("user_message", "")
    node_id = data.get("node_id")
    
    if not user_message:
        raise HTTPException(status_code=400, detail="user_message required")
    
    try:
        node = await story_service.get_story_node(node_id) if node_id else None
        choices = node.get("choices", []) if node else data.get("choices", [])
        
        if not choices:
            return {
                "matched": False,
                "reason": "no_choices_available",
                "confidence": 0.0
            }
        
        result = await choice_matcher.match(
            user_message=user_message,
            choices=choices,
            threshold=0.7,
            use_llm_fallback=True
        )
        
        response = {
            "matched": result.matched,
            "confidence": result.confidence,
            "method": result.method
        }
        
        if result.matched and result.choice:
            response["choice"] = result.choice
            response["choice_id"] = result.choice.get("id")
            response["choice_text"] = result.choice.get("text")
            response["next_node_id"] = result.choice.get("next_node_id")
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{story_id}/ending/check")
async def check_story_ending(
    request: Request,
    story_id: str,
    data: dict[str, Any]
) -> dict[str, Any]:
    progress_id = data.get("progress_id")
    
    if not progress_id:
        raise HTTPException(status_code=400, detail="progress_id required")
    
    try:
        result = await story_service.determine_ending(progress_id)
        
        response = {
            "is_ending": result.is_ending
        }
        
        if result.is_ending:
            response["ending_type"] = result.ending_type
            response["rewards"] = result.rewards
            response["completion_time_minutes"] = result.completion_time_minutes
            response["narrative"] = result.narrative
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{story_id}/endings/preview")
async def preview_possible_endings(
    request: Request,
    story_id: str
) -> dict[str, Any]:
    try:
        endings = await story_service.get_possible_endings(story_id)
        
        return {
            "story_id": story_id,
            "possible_endings": endings,
            "total": len(endings)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/progress/{character_id}")
async def get_story_progress(request: Request, character_id: str) -> dict[str, Any]:
    return {
        "character_id": character_id,
        "current_story_id": "story_001",
        "current_node_id": "node_003",
        "progress": 0.5,
    }


@router.post("/{story_id}/storyboard/generate", response_model=Task)
async def generate_storyboard(request: Request, story_id: str) -> Task:
    return Task(
        id="task_storyboard",
        type="storyboard_generation",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("", response_model=Story)
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


@router.put("/{story_id}", response_model=Story)
async def update_story(request: Request, story_id: str, data: StoryUpdate) -> Story:
    return Story(
        id=story_id,
        title=data.title or "Updated Story",
        slug=data.slug,
        description=data.description,
        character_id="char_001",
        nodes=data.nodes or [],
        created_at=datetime.now(),
    )


@router.delete("/{story_id}", response_model=BaseResponse)
async def delete_story(request: Request, story_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Story deleted")


@router.post("/{story_id}/nodes", response_model=BaseResponse)
async def create_story_node(
    request: Request, 
    story_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    return BaseResponse(success=True, message="Story node created")


@router.put("/nodes/{node_id}", response_model=BaseResponse)
async def update_story_node(
    request: Request, 
    node_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    return BaseResponse(success=True, message="Story node updated")


@router.delete("/nodes/{node_id}", response_model=BaseResponse)
async def delete_story_node(request: Request, node_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Story node deleted")


admin_story_router = APIRouter(prefix="/api/stories/admin", tags=["stories-admin"])


@admin_story_router.post("/create", response_model=Story)
async def admin_create_story(request: Request, data: StoryCreate) -> Story:
    return Story(
        id="story_admin_new",
        title=data.title,
        slug=data.slug,
        description=data.description,
        character_id=data.character_id,
        created_at=datetime.now(),
    )


@admin_story_router.put("/{story_id}", response_model=Story)
async def admin_update_story(
    request: Request, 
    story_id: str, 
    data: StoryUpdate
) -> Story:
    return Story(
        id=story_id,
        title=data.title or "Admin Updated Story",
        slug=data.slug,
        description=data.description,
        character_id="char_001",
        created_at=datetime.now(),
    )


@admin_story_router.delete("/{story_id}", response_model=BaseResponse)
async def admin_delete_story(request: Request, story_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Story deleted by admin")


@router.post("/{story_id}/replay")
async def replay_story(
    request: Request,
    story_id: str,
    data: dict[str, Any]
) -> dict[str, Any]:
    session_id = data.get("session_id")
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    story = await story_service.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    if session_id:
        await db.execute(
            "UPDATE story_progress SET archived = 1 WHERE user_id = ? AND story_id = ? AND archived = 0",
            (user_id, story_id)
        )
    
    play_index = await story_service.get_next_play_index(user_id, story_id)
    
    progress_id = f"prog_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    start_node_id = story.get("start_node_id")
    
    await db.execute(
        """INSERT INTO story_progress 
           (id, user_id, story_id, character_id, status, current_node_id, visited_nodes, choices_made, started_at, last_played_at, play_index, archived)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)""",
        (
            progress_id,
            user_id,
            story_id,
            story.get("character_id"),
            "in_progress",
            start_node_id,
            json.dumps([start_node_id]) if start_node_id else "[]",
            "[]",
            now,
            now,
            play_index
        )
    )
    
    await story_service.increment_play_count(story_id)
    
    return {
        "progress_id": progress_id,
        "play_index": play_index,
        "start_node_id": start_node_id,
        "opening_message": story.get("description", "A new adventure begins...")
    }


@router.get("/{story_id}/history")
async def get_play_history(
    request: Request,
    story_id: str
) -> list[dict[str, Any]]:
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    history = await story_service.get_play_history(user_id, story_id)
    return history


@router.get("/{story_id}/history/{progress_id}")
async def get_play_detail(
    request: Request,
    story_id: str,
    progress_id: str
) -> dict[str, Any]:
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    row = await db.execute(
        """SELECT sp.*, s.title as story_title
           FROM story_progress sp
           LEFT JOIN stories s ON sp.story_id = s.id
           WHERE sp.id = ? AND sp.user_id = ? AND sp.story_id = ?""",
        (progress_id, user_id, story_id),
        fetch=True
    )
    
    if not row:
        raise HTTPException(status_code=404, detail="Play history not found")
    
    result = dict(row)
    
    for field in ["visited_nodes", "choices_made"]:
        if result.get(field) and isinstance(result[field], str):
            try:
                result[field] = json.loads(result[field])
            except json.JSONDecodeError:
                result[field] = []
    
    choices = result.get("choices_made", [])
    result["choices_count"] = len(choices) if isinstance(choices, list) else 0
    
    return result


@router.post("/{story_id}/archive-progress")
async def archive_current_progress(
    request: Request,
    story_id: str
) -> dict[str, Any]:
    user_id = getattr(request.state, "user_id", None)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    result = await db.execute(
        "UPDATE story_progress SET archived = 1 WHERE user_id = ? AND story_id = ? AND archived = 0",
        (user_id, story_id)
    )
    
    return {
        "success": True,
        "message": "Progress archived"
    }
