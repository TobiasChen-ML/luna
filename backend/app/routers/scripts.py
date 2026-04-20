from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any

from app.models import BaseResponse
from app.services.media_trigger_service import media_trigger_service

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


@router.get("")
async def list_scripts(request: Request) -> list[dict[str, Any]]:
    return [
        {
            "id": "script_001",
            "title": "Sample Script",
            "description": "A sample script",
            "content": "Script content here...",
            "creator_id": "creator_001",
            "is_public": True,
            "created_at": datetime.now().isoformat(),
        }
    ]


@router.post("", response_model=dict[str, Any])
async def create_script(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "script_new",
        "title": data.get("title", "New Script"),
        "description": data.get("description", ""),
        "character_id": data.get("character_id", ""),
        "genre": data.get("genre", ""),
        "world_setting": data.get("world_setting", ""),
        "user_role": data.get("user_role", ""),
        "user_role_description": data.get("user_role_description", ""),
        "opening_line": data.get("opening_line", ""),
        "scenes": data.get("scenes", []),
        "npcs": data.get("npcs", []),
        "triggers": data.get("triggers", []),
        "tags": data.get("tags", []),
        "status": "draft",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@router.get("/{script_id}")
async def get_script(request: Request, script_id: str) -> dict[str, Any]:
    return {
        "id": script_id,
        "title": "Sample Script",
        "description": "A sample script",
        "character_id": "char_001",
        "genre": "romance",
        "world_setting": "Modern City",
        "user_role": "Main Character",
        "user_role_description": "The protagonist",
        "opening_line": "Hello there!",
        "scenes": [],
        "npcs": [],
        "triggers": [],
        "tags": ["romance"],
        "play_count": 0,
        "likes": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }


@router.put("/{script_id}")
async def update_script(
    request: Request, 
    script_id: str, 
    data: dict[str, Any]
) -> dict[str, Any]:
    return {
        "id": script_id,
        "title": data.get("title", "Updated Script"),
        "description": data.get("description", ""),
        "character_id": data.get("character_id", ""),
        "genre": data.get("genre", ""),
        "updated_at": datetime.now().isoformat(),
    }


@router.delete("/{script_id}", response_model=BaseResponse)
async def delete_script(request: Request, script_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Script deleted")


@router.get("/character/{character_id}")
async def get_character_scripts(
    request: Request, 
    character_id: str
) -> dict[str, Any]:
    return {
        "scripts": [
            {
                "id": "script_001",
                "title": "Character Script",
                "character_id": character_id,
                "status": "published",
                "created_at": datetime.now().isoformat(),
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
    }


@router.get("/user/my-scripts")
async def get_my_scripts(request: Request) -> dict[str, Any]:
    return {
        "scripts": [
            {
                "id": "script_001",
                "title": "My Script",
                "character_id": "char_001",
                "status": "published",
                "created_at": datetime.now().isoformat(),
            }
        ],
        "total": 1,
        "page": 1,
        "page_size": 20,
        "total_pages": 1,
    }


@router.post("/{script_id}/start")
async def start_script(
    request: Request, 
    script_id: str, 
    data: dict[str, Any]
) -> dict[str, Any]:
    return {
        "session_state": {"script_id": script_id},
        "opening_message": "Welcome to the story!",
        "progress_id": f"progress_{script_id}",
    }


@router.get("/{script_id}/progress")
async def get_script_progress(request: Request, script_id: str) -> dict[str, Any]:
    return {
        "id": f"progress_{script_id}",
        "user_id": "user_001",
        "script_id": script_id,
        "character_id": "char_001",
        "current_scene_id": "scene_001",
        "variables": {
            "relationship_type": "romantic",
            "tension_level": "medium",
            "custom_vars": {},
            "unlocked_scenes": [],
            "triggered_events": [],
            "progress": 0.5,
        },
        "relationship_metrics": {
            "affection": 50,
            "trust": 60,
            "intimacy": 40,
        },
        "session_count": 1,
        "total_turns": 10,
        "started_at": datetime.now().isoformat(),
        "last_played_at": datetime.now().isoformat(),
    }


@router.get("/user/progress")
async def get_all_user_progress(request: Request) -> list[dict[str, Any]]:
    return [
        {
            "id": "progress_001",
            "script_id": "script_001",
            "character_id": "char_001",
            "current_scene_id": "scene_001",
            "progress": 0.5,
        }
    ]


@router.get("/{script_id}/relationship-stage")
async def get_relationship_stage(request: Request, script_id: str) -> dict[str, Any]:
    return {
        "script_id": script_id,
        "metrics": {
            "affection": 50,
            "trust": 60,
            "intimacy": 40,
        },
        "current_stage": "Build",
        "next_stage": "Climax",
        "progress": 0.5,
        "requirements": {
            "affection": 70,
            "trust": 70,
            "intimacy": 60,
        },
    }


@router.get("/{script_id}/gates")
async def check_emotion_gates(request: Request, script_id: str) -> dict[str, Any]:
    return {
        "script_id": script_id,
        "gates": {
            "trust": {
                "passed": True,
                "current": 60,
                "required": 50,
            },
            "intimacy": {
                "passed": False,
                "current": 40,
                "required": 60,
            },
        },
    }


@router.post("/{script_id}/load-dag")
async def load_dag(request: Request, script_id: str) -> dict[str, Any]:
    return {
        "script_id": script_id,
        "nodes": 10,
        "edges": 15,
        "start_node": "node_001",
    }


@router.get("/{script_id}/dag/validate")
async def validate_dag(request: Request, script_id: str) -> dict[str, Any]:
    return {
        "script_id": script_id,
        "valid": True,
        "errors": [],
    }


@router.get("/{script_id}/dag/endings")
async def get_endings(request: Request, script_id: str) -> dict[str, Any]:
    return {
        "script_id": script_id,
        "endings": [
            {
                "node_id": "ending_001",
                "name": "Happy Ending",
                "ending_type": "positive",
            },
            {
                "node_id": "ending_002",
                "name": "Bittersweet Ending",
                "ending_type": "neutral",
            },
        ],
    }


@router.post("/publish", response_model=BaseResponse)
async def publish_script(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Script published")


@router.post("/{script_id}/media/trigger")
async def trigger_script_media(
    request: Request,
    script_id: str,
    data: dict[str, Any]
) -> dict[str, Any]:
    node_id = data.get("node_id")
    cue_id = data.get("cue_id")
    session_id = data.get("session_id")
    character_id = data.get("character_id")
    
    if not all([node_id, cue_id, session_id, character_id]):
        raise HTTPException(
            status_code=400,
            detail="node_id, cue_id, session_id, and character_id required"
        )
    
    user_id = getattr(request.state, "user_id", "guest")
    
    try:
        result = await media_trigger_service.trigger_media(
            script_id=script_id,
            node_id=node_id,
            cue_id=cue_id,
            session_id=session_id,
            user_id=user_id,
            character_id=character_id
        )
        
        if not result.get("allowed"):
            return {
                "success": False,
                "reason": result.get("reason"),
                "error": result.get("error")
            }
        
        return {
            "success": True,
            "task_id": result.get("task_id"),
            "media_type": result.get("media_type"),
            "image_url": result.get("image_url"),
            "video_url": result.get("video_url"),
            "estimated_seconds": result.get("estimated_seconds")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{script_id}/media/check")
async def check_media_trigger(
    request: Request,
    script_id: str,
    data: dict[str, Any]
) -> dict[str, Any]:
    node_id = data.get("node_id")
    cue_id = data.get("cue_id")
    session_id = data.get("session_id")
    
    if not all([node_id, cue_id, session_id]):
        raise HTTPException(
            status_code=400,
            detail="node_id, cue_id, and session_id required"
        )
    
    try:
        result = await media_trigger_service.can_trigger(
            script_id=script_id,
            node_id=node_id,
            cue_id=cue_id,
            session_id=session_id
        )
        
        return {
            "allowed": result.get("allowed"),
            "reason": result.get("reason"),
            "media_cue": result.get("media_cue")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{script_id}/media/task/{task_id}")
async def get_media_task_status(
    request: Request,
    script_id: str,
    task_id: str
) -> dict[str, Any]:
    try:
        task = await media_trigger_service.get_task_status(task_id)
        
        if not task:
            return {
                "found": False,
                "task_id": task_id
            }
        
        return {
            "found": True,
            "task_id": task_id,
            "status": task.get("status"),
            "type": task.get("type"),
            "result": task.get("result")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
