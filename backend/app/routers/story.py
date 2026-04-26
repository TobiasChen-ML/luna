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


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.utcnow()
    return datetime.utcnow()


def _json_loads(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return default


def _normalize_story_row(row: dict[str, Any]) -> Story:
    return Story(
        id=row.get("id", ""),
        title=row.get("title", ""),
        slug=row.get("slug"),
        description=row.get("description"),
        character_id=row.get("character_id", ""),
        status=row.get("status", StoryStatus.DRAFT),
        created_at=_parse_datetime(row.get("created_at")),
        updated_at=_parse_datetime(row.get("updated_at")) if row.get("updated_at") else None,
    )


async def _load_story_nodes(story_id: str) -> list[dict[str, Any]]:
    rows = await db.execute(
        "SELECT * FROM story_nodes WHERE story_id = ? ORDER BY sequence ASC, created_at ASC",
        (story_id,),
        fetch_all=True,
    )
    normalized: list[dict[str, Any]] = []
    for row in rows:
        node = dict(row)
        node["choices"] = _json_loads(node.get("choices"), [])
        node["character_context"] = _json_loads(node.get("character_context"), {})
        node["auto_advance"] = _json_loads(node.get("auto_advance"), {})
        node["trigger_conditions"] = _json_loads(node.get("trigger_conditions"), {})
        normalized.append(node)
    return normalized


@router.get("/available/{character_id}")
async def get_available_stories(request: Request, character_id: str) -> list[Story]:
    rows = await db.execute(
        "SELECT * FROM stories WHERE character_id = ? AND status = ? ORDER BY created_at DESC",
        (character_id, StoryStatus.PUBLISHED.value),
        fetch_all=True,
    )
    return [_normalize_story_row(row) for row in rows]


@router.get("/character/{character_id}")
async def get_character_stories(
    request: Request,
    character_id: str,
    include_drafts: bool = False,
) -> list[Story]:
    if include_drafts:
        rows = await db.execute(
            "SELECT * FROM stories WHERE character_id = ? ORDER BY created_at DESC",
            (character_id,),
            fetch_all=True,
        )
    else:
        rows = await db.execute(
            "SELECT * FROM stories WHERE character_id = ? AND status = ? ORDER BY created_at DESC",
            (character_id, StoryStatus.PUBLISHED.value),
            fetch_all=True,
        )
    return [_normalize_story_row(row) for row in rows]


@router.get("/{story_id}", response_model=Story)
async def get_story(request: Request, story_id: str) -> Story:
    row = await db.execute("SELECT * FROM stories WHERE id = ?", (story_id,), fetch=True)
    if not row:
        return Story(
            id=story_id,
            title="Story",
            slug="story",
            character_id="char_001",
            created_at=datetime.utcnow(),
        )
    return _normalize_story_row(row)


@router.get("/{story_id}/nodes")
async def get_story_nodes(request: Request, story_id: str) -> list[dict[str, Any]]:
    story = await db.execute("SELECT id FROM stories WHERE id = ?", (story_id,), fetch=True)
    if not story:
        return [
            {
                "id": "node_001",
                "story_id": story_id,
                "scene_description": "Story node content",
                "choices": [{"id": "choice_001", "text": "Choice A", "next_node_id": "node_002"}],
            }
        ]
    return await _load_story_nodes(story_id)


@router.post("/{story_id}/start")
async def start_story(request: Request, story_id: str) -> dict[str, Any]:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {"success": True, "message": "Story started", "story_id": story_id}

    story = await story_service.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    progress = await story_service.get_progress(user_id, story_id)
    if not progress:
        start_node_id = story.get("start_node_id")
        if not start_node_id:
            first_node = await db.execute(
                "SELECT id FROM story_nodes WHERE story_id = ? ORDER BY sequence ASC, created_at ASC LIMIT 1",
                (story_id,),
                fetch=True,
            )
            start_node_id = first_node.get("id") if first_node else None
        if not start_node_id:
            raise HTTPException(status_code=400, detail="Story has no start node")

        progress = await story_service.create_progress(
            user_id=user_id,
            story_id=story_id,
            character_id=story.get("character_id"),
            start_node_id=start_node_id,
        )

    current_node_id = progress.get("current_node_id") or story.get("start_node_id")
    current_node = await story_service.get_story_node(current_node_id) if current_node_id else None
    story_nodes = await _load_story_nodes(story_id)

    return {
        "success": True,
        "story": {
            **story,
            "entry_conditions": _json_loads(story.get("entry_conditions"), {}),
            "completion_rewards": _json_loads(story.get("completion_rewards"), {}),
            "ai_trigger_keywords": _json_loads(story.get("ai_trigger_keywords"), []),
            "total_nodes": len(story_nodes),
        },
        "current_node": current_node,
        "progress": progress,
    }


@router.post("/{story_id}/resume")
async def resume_story(request: Request, story_id: str) -> dict[str, Any]:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {"success": True, "message": "Story resumed", "story_id": story_id}

    story = await story_service.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    progress = await story_service.get_progress(user_id, story_id)
    if not progress:
        return await start_story(request, story_id)

    current_node_id = progress.get("current_node_id") or story.get("start_node_id")
    current_node = await story_service.get_story_node(current_node_id) if current_node_id else None
    story_nodes = await _load_story_nodes(story_id)

    return {
        "success": True,
        "story": {
            **story,
            "entry_conditions": _json_loads(story.get("entry_conditions"), {}),
            "completion_rewards": _json_loads(story.get("completion_rewards"), {}),
            "ai_trigger_keywords": _json_loads(story.get("ai_trigger_keywords"), []),
            "total_nodes": len(story_nodes),
        },
        "current_node": current_node,
        "progress": progress,
    }


@router.post("/{story_id}/choice")
async def make_story_choice(
    request: Request, 
    story_id: str, 
    data: dict[str, Any]
) -> dict[str, Any]:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {
            "story_id": story_id,
            "next_node_id": "node_002",
            "content": "Next story content",
            "choices": [],
        }

    choice_id = data.get("choice_id")
    progress = await story_service.get_progress(user_id, story_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    current_node_id = progress.get("current_node_id")
    if not current_node_id:
        raise HTTPException(status_code=400, detail="Current story node is missing")
    current_node = await story_service.get_story_node(current_node_id)
    if not current_node:
        raise HTTPException(status_code=404, detail="Current story node not found")

    choices = current_node.get("choices", []) or []
    selected_choice = None
    for choice in choices:
        if str(choice.get("id")) == str(choice_id):
            selected_choice = choice
            break

    if not selected_choice:
        raise HTTPException(status_code=400, detail="Choice not found")

    next_node_id = selected_choice.get("next_node_id")
    if not next_node_id:
        raise HTTPException(status_code=400, detail="Selected choice has no next node")

    choice_record = {
        "node_id": current_node_id,
        "choice_id": selected_choice.get("id"),
        "text": selected_choice.get("text"),
        "effects": selected_choice.get("effects", {}),
        "timestamp": datetime.utcnow().isoformat(),
    }
    await story_service.update_progress(
        progress["id"],
        node_id=next_node_id,
        choice_made=choice_record,
    )

    next_node = await story_service.get_story_node(next_node_id)
    updated_progress = await story_service.get_progress(user_id, story_id)
    is_ending = bool(next_node and next_node.get("is_ending_node"))

    result: dict[str, Any] = {
        "story_id": story_id,
        "next_node_id": next_node_id,
        "next_node": next_node,
        "progress": updated_progress,
        "is_ending": is_ending,
    }
    if is_ending:
        ending_result = await story_service.determine_ending(progress["id"])
        result["ending"] = {
            "type": ending_result.ending_type,
            "rewards": ending_result.rewards,
            "completion_time_minutes": ending_result.completion_time_minutes,
            "narrative": ending_result.narrative,
        }
    return result


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
async def get_story_progress(request: Request, character_id: str) -> Any:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        return {
            "character_id": character_id,
            "current_story_id": "story_001",
            "current_node_id": "node_003",
            "progress": 0.5,
        }

    rows = await db.execute(
        """
        SELECT sp.*, s.title AS story_title, s.total_nodes
        FROM story_progress sp
        JOIN stories s ON s.id = sp.story_id
        WHERE sp.user_id = ? AND sp.character_id = ? AND sp.archived = 0
        ORDER BY sp.last_played_at DESC
        """,
        (user_id, character_id),
        fetch_all=True,
    )
    progress_list: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        visited = _json_loads(item.get("visited_nodes"), [])
        choices = _json_loads(item.get("choices_made"), [])
        total_nodes = int(item.get("total_nodes") or 0)
        completion_pct = 0.0
        if total_nodes > 0:
            completion_pct = min(1.0, len(visited) / total_nodes)
        item["visited_nodes"] = visited
        item["choices_made"] = choices
        item["completion_percentage"] = completion_pct
        progress_list.append(item)
    return progress_list


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
    story_id = f"story_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    base_slug = (data.slug or data.title.lower().strip().replace(" ", "-"))[:100] or "story"
    slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"

    await db.execute(
        """
        INSERT INTO stories (
            id, character_id, title, slug, description, status, author_type, author_id,
            is_official, total_nodes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            story_id,
            data.character_id,
            data.title,
            slug,
            data.description,
            StoryStatus.DRAFT.value,
            "user",
            getattr(request.state, "user_id", None),
            0,
            len(data.nodes or []),
            now,
            now,
        ),
    )

    start_node_id: Optional[str] = None
    for index, node in enumerate(data.nodes or []):
        node_id = str(node.get("id") or f"node_{uuid.uuid4().hex[:12]}")
        if index == 0:
            start_node_id = node_id
        await db.execute(
            """
            INSERT INTO story_nodes (
                id, story_id, sequence, title, narrative_phase, location, scene_description,
                character_context, response_instructions, max_turns_in_node, choices, auto_advance,
                is_ending_node, ending_type, trigger_image, image_prompt_hint, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                story_id,
                int(node.get("sequence", index)),
                node.get("title"),
                node.get("narrative_phase", "opening"),
                node.get("location"),
                node.get("scene_description"),
                json.dumps(node.get("character_context", {}), ensure_ascii=False),
                node.get("response_instructions"),
                int(node.get("max_turns_in_node", 3)),
                json.dumps(node.get("choices", []), ensure_ascii=False),
                json.dumps(node.get("auto_advance", {}), ensure_ascii=False),
                1 if node.get("is_ending_node") else 0,
                node.get("ending_type"),
                1 if node.get("trigger_image") else 0,
                node.get("image_prompt_hint"),
                now,
                now,
            ),
        )

    if start_node_id:
        await db.execute(
            "UPDATE stories SET start_node_id = ?, updated_at = ? WHERE id = ?",
            (start_node_id, now, story_id),
        )

    row = await db.execute("SELECT * FROM stories WHERE id = ?", (story_id,), fetch=True)
    return _normalize_story_row(row)


@router.put("/{story_id}", response_model=Story)
async def update_story(request: Request, story_id: str, data: StoryUpdate) -> Story:
    existing = await db.execute("SELECT * FROM stories WHERE id = ?", (story_id,), fetch=True)
    if not existing:
        return Story(
            id=story_id,
            title=data.title or "Updated Story",
            slug=data.slug,
            description=data.description,
            character_id="char_001",
            nodes=data.nodes or [],
            created_at=datetime.utcnow(),
        )

    now = datetime.utcnow().isoformat()
    await db.execute(
        """
        UPDATE stories
        SET title = ?, slug = ?, description = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            data.title if data.title is not None else existing.get("title"),
            data.slug if data.slug is not None else existing.get("slug"),
            data.description if data.description is not None else existing.get("description"),
            now,
            story_id,
        ),
    )

    if data.nodes is not None:
        await db.execute("DELETE FROM story_nodes WHERE story_id = ?", (story_id,))
        start_node_id: Optional[str] = None
        for index, node in enumerate(data.nodes):
            node_id = str(node.get("id") or f"node_{uuid.uuid4().hex[:12]}")
            if index == 0:
                start_node_id = node_id
            await db.execute(
                """
                INSERT INTO story_nodes (
                    id, story_id, sequence, title, narrative_phase, location, scene_description,
                    character_context, response_instructions, max_turns_in_node, choices, auto_advance,
                    is_ending_node, ending_type, trigger_image, image_prompt_hint, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    node_id,
                    story_id,
                    int(node.get("sequence", index)),
                    node.get("title"),
                    node.get("narrative_phase", "opening"),
                    node.get("location"),
                    node.get("scene_description"),
                    json.dumps(node.get("character_context", {}), ensure_ascii=False),
                    node.get("response_instructions"),
                    int(node.get("max_turns_in_node", 3)),
                    json.dumps(node.get("choices", []), ensure_ascii=False),
                    json.dumps(node.get("auto_advance", {}), ensure_ascii=False),
                    1 if node.get("is_ending_node") else 0,
                    node.get("ending_type"),
                    1 if node.get("trigger_image") else 0,
                    node.get("image_prompt_hint"),
                    now,
                    now,
                ),
            )
        await db.execute(
            "UPDATE stories SET start_node_id = ?, total_nodes = ?, updated_at = ? WHERE id = ?",
            (start_node_id, len(data.nodes), now, story_id),
        )

    row = await db.execute("SELECT * FROM stories WHERE id = ?", (story_id,), fetch=True)
    return _normalize_story_row(row)


@router.delete("/{story_id}", response_model=BaseResponse)
async def delete_story(request: Request, story_id: str) -> BaseResponse:
    existing = await db.execute("SELECT id FROM stories WHERE id = ?", (story_id,), fetch=True)
    if not existing:
        return BaseResponse(success=True, message="Story deleted")
    await db.execute("DELETE FROM story_nodes WHERE story_id = ?", (story_id,))
    await db.execute("DELETE FROM story_progress WHERE story_id = ?", (story_id,))
    await db.execute("DELETE FROM stories WHERE id = ?", (story_id,))
    return BaseResponse(success=True, message="Story deleted")


@router.post("/{story_id}/nodes")
async def create_story_node(
    request: Request, 
    story_id: str, 
    data: dict[str, Any]
) -> dict[str, Any]:
    story = await db.execute("SELECT id FROM stories WHERE id = ?", (story_id,), fetch=True)
    if not story:
        return {"success": True, "message": "Story node created"}

    now = datetime.utcnow().isoformat()
    node_id = str(data.get("id") or f"node_{uuid.uuid4().hex[:12]}")
    sequence = int(data.get("sequence", 0))
    await db.execute(
        """
        INSERT INTO story_nodes (
            id, story_id, sequence, title, narrative_phase, location, scene_description,
            character_context, response_instructions, max_turns_in_node, choices, auto_advance,
            is_ending_node, ending_type, trigger_image, image_prompt_hint, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            node_id,
            story_id,
            sequence,
            data.get("title"),
            data.get("narrative_phase", "opening"),
            data.get("location"),
            data.get("scene_description"),
            json.dumps(data.get("character_context", {}), ensure_ascii=False),
            data.get("response_instructions"),
            int(data.get("max_turns_in_node", 3)),
            json.dumps(data.get("choices", []), ensure_ascii=False),
            json.dumps(data.get("auto_advance", {}), ensure_ascii=False),
            1 if data.get("is_ending_node") else 0,
            data.get("ending_type"),
            1 if data.get("trigger_image") else 0,
            data.get("image_prompt_hint"),
            now,
            now,
        ),
    )
    total = await db.execute(
        "SELECT COUNT(1) as c FROM story_nodes WHERE story_id = ?",
        (story_id,),
        fetch=True,
    )
    await db.execute(
        "UPDATE stories SET total_nodes = ?, updated_at = ? WHERE id = ?",
        (int(total.get("c", 0)), now, story_id),
    )
    return {"success": True, "message": "Story node created", "id": node_id}


@router.post("/nodes")
async def create_story_node_v2(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    story_id = data.get("story_id")
    if not story_id:
        raise HTTPException(status_code=400, detail="story_id is required")
    await create_story_node(request, str(story_id), data)
    node_id = str(data.get("id") or "")
    if node_id:
        node = await story_service.get_story_node(node_id)
        if node:
            return node
    return {"id": node_id}


@router.put("/nodes/{node_id}")
async def update_story_node(
    request: Request, 
    node_id: str, 
    data: dict[str, Any]
) -> dict[str, Any]:
    existing = await db.execute("SELECT * FROM story_nodes WHERE id = ?", (node_id,), fetch=True)
    if not existing:
        return {"success": True, "message": "Story node updated"}

    now = datetime.utcnow().isoformat()
    await db.execute(
        """
        UPDATE story_nodes
        SET sequence = ?, title = ?, narrative_phase = ?, location = ?, scene_description = ?,
            character_context = ?, response_instructions = ?, max_turns_in_node = ?, choices = ?,
            auto_advance = ?, is_ending_node = ?, ending_type = ?, trigger_image = ?,
            image_prompt_hint = ?, updated_at = ?
        WHERE id = ?
        """,
        (
            int(data.get("sequence", existing.get("sequence", 0))),
            data.get("title", existing.get("title")),
            data.get("narrative_phase", existing.get("narrative_phase", "opening")),
            data.get("location", existing.get("location")),
            data.get("scene_description", existing.get("scene_description")),
            json.dumps(data.get("character_context", _json_loads(existing.get("character_context"), {})), ensure_ascii=False),
            data.get("response_instructions", existing.get("response_instructions")),
            int(data.get("max_turns_in_node", existing.get("max_turns_in_node", 3))),
            json.dumps(data.get("choices", _json_loads(existing.get("choices"), [])), ensure_ascii=False),
            json.dumps(data.get("auto_advance", _json_loads(existing.get("auto_advance"), {})), ensure_ascii=False),
            1 if data.get("is_ending_node", bool(existing.get("is_ending_node"))) else 0,
            data.get("ending_type", existing.get("ending_type")),
            1 if data.get("trigger_image", bool(existing.get("trigger_image"))) else 0,
            data.get("image_prompt_hint", existing.get("image_prompt_hint")),
            now,
            node_id,
        ),
    )
    return {"success": True, "message": "Story node updated", "id": node_id}


@router.delete("/nodes/{node_id}", response_model=BaseResponse)
async def delete_story_node(request: Request, node_id: str) -> BaseResponse:
    existing = await db.execute("SELECT story_id FROM story_nodes WHERE id = ?", (node_id,), fetch=True)
    if not existing:
        return BaseResponse(success=True, message="Story node deleted")
    await db.execute("DELETE FROM story_nodes WHERE id = ?", (node_id,))
    total = await db.execute(
        "SELECT COUNT(1) as c FROM story_nodes WHERE story_id = ?",
        (existing.get("story_id"),),
        fetch=True,
    )
    await db.execute(
        "UPDATE stories SET total_nodes = ?, updated_at = ? WHERE id = ?",
        (int(total.get("c", 0)), datetime.utcnow().isoformat(), existing.get("story_id")),
    )
    return BaseResponse(success=True, message="Story node deleted")


admin_story_router = APIRouter(prefix="/api/stories/admin", tags=["stories-admin"])


@admin_story_router.post("/create", response_model=Story)
async def admin_create_story(request: Request, data: StoryCreate) -> Story:
    return await create_story(request, data)


@admin_story_router.put("/{story_id}", response_model=Story)
async def admin_update_story(
    request: Request, 
    story_id: str, 
    data: StoryUpdate
) -> Story:
    return await update_story(request, story_id, data)


@admin_story_router.delete("/{story_id}", response_model=BaseResponse)
async def admin_delete_story(request: Request, story_id: str) -> BaseResponse:
    return await delete_story(request, story_id)


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
