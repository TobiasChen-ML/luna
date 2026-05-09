from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Query
from typing import Any, Optional

from app.models import BaseResponse
from app.services.media_trigger_service import media_trigger_service
from app.services.script_service import script_service
from app.core.database import db

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


def _get_user_id(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    return str(user_id) if user_id else "guest"


async def _session_belongs_to_user(session_id: str | None, user_id: str) -> bool:
    if not session_id:
        return False
    row = await db.execute(
        "SELECT id FROM chat_sessions WHERE id = ? AND user_id = ?",
        (session_id, user_id),
        fetch=True,
    )
    return bool(row)


async def _assert_script_access(script: dict[str, Any], request: Request) -> None:
    source_session_id = script.get("source_session_id")
    if not source_session_id:
        if script.get("is_public") is False:
            raise HTTPException(status_code=403, detail="Script is private")
        return
    user_id = _get_user_id(request)
    if user_id == "guest" or not await _session_belongs_to_user(source_session_id, user_id):
        raise HTTPException(status_code=403, detail="Script does not belong to this user")


@router.get("")
async def list_scripts(
    request: Request,
    source_session_id: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    if source_session_id:
        if not await _session_belongs_to_user(source_session_id, _get_user_id(request)):
            raise HTTPException(status_code=403, detail="Session does not belong to this user")
        rows = await db.execute(
            """
            SELECT *
            FROM scripts
            WHERE source_session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (source_session_id, limit),
            fetch_all=True,
        )
    else:
        rows = await db.execute(
            """
            SELECT *
            FROM scripts
            WHERE source_session_id IS NULL
              AND is_public = 1
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
            fetch_all=True,
        )

    items = [script_service._row_to_dict(row) for row in (rows or [])]
    return {"items": items, "total": len(items)}


@router.post("", response_model=dict[str, Any])
async def create_script(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    from app.models.script import ScriptCreate

    try:
        return await script_service.create_script(ScriptCreate(**data))
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{script_id}/nodes")
async def get_script_nodes(request: Request, script_id: str) -> dict[str, Any]:
    script = await script_service.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    await _assert_script_access(script, request)
    nodes = await script_service.list_nodes(script_id)
    return {"script_id": script_id, "nodes": nodes}


@router.get("/{script_id}")
async def get_script(request: Request, script_id: str) -> dict[str, Any]:
    script = await script_service.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    await _assert_script_access(script, request)
    return script


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
