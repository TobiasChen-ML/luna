import json
import logging
import uuid
from typing import Optional, Any
from datetime import datetime

from app.core.database import db
from app.models.script import (
    ScriptCreate,
    ScriptUpdate,
    ScriptNodeCreate,
    ScriptNodeUpdate,
    ScriptSessionState,
    ScriptStatus,
    ScriptState,
    ScriptReviewCreate,
    ReviewAction,
    generate_script_id,
    generate_node_id,
)

logger = logging.getLogger(__name__)


def generate_review_id() -> str:
    return f"review_{uuid.uuid4().hex[:12]}"


class ScriptService:
    _instance = None
    
    def __init__(self):
        pass
    
    @classmethod
    def get_instance(cls) -> "ScriptService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def get_script(self, script_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM scripts WHERE id = ?",
            (script_id,),
            fetch=True
        )
        return self._row_to_dict(row) if row else None
    
    async def get_script_by_slug(self, slug: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM scripts WHERE slug = ?",
            (slug,),
            fetch=True
        )
        return self._row_to_dict(row) if row else None
    
    async def list_scripts(
        self,
        character_id: Optional[str] = None,
        status: Optional[str] = None,
        is_public: Optional[bool] = None,
    ) -> list[dict]:
        conditions = ["1=1"]
        params = []
        
        if character_id:
            conditions.append("character_id = ?")
            params.append(character_id)
        if status:
            conditions.append("status = ?")
            params.append(status)
        if is_public is not None:
            conditions.append("is_public = ?")
            params.append(1 if is_public else 0)
        
        query = f"SELECT * FROM scripts WHERE {' AND '.join(conditions)} ORDER BY created_at DESC"
        rows = await db.execute(query, tuple(params), fetch_all=True)
        return [self._row_to_dict(row) for row in rows]
    
    async def create_script(self, data: ScriptCreate) -> dict:
        script_id = generate_script_id()
        now = datetime.utcnow().isoformat()
        
        slug = data.slug or script_id
        
        await db.execute(
            """INSERT INTO scripts
               (id, character_id, title, slug, genre, world_setting, world_rules,
                character_role, character_setting, user_role, user_role_description,
                start_node_id, opening_scene, opening_line, emotion_gates, triggers,
                tags, difficulty, estimated_duration, is_public, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 'draft', ?, ?)""",
            (
                script_id,
                data.character_id,
                data.title,
                slug,
                data.genre,
                data.world_setting,
                json.dumps(data.world_rules) if data.world_rules else None,
                data.character_role,
                json.dumps(data.character_setting) if data.character_setting else None,
                data.user_role,
                data.user_role_description,
                data.start_node_id,
                data.opening_scene,
                data.opening_line,
                json.dumps(data.emotion_gates) if data.emotion_gates else None,
                json.dumps(data.triggers) if data.triggers else None,
                json.dumps(data.tags) if data.tags else None,
                data.difficulty,
                data.estimated_duration,
                now,
                now,
            )
        )
        
        logger.info(f"Created script: {script_id} - {data.title}")
        return await self.get_script(script_id)
    
    async def update_script(self, script_id: str, data: ScriptUpdate) -> Optional[dict]:
        existing = await self.get_script(script_id)
        if not existing:
            return None
        
        updates = []
        params = []
        
        for field in ["title", "genre", "world_setting", "character_role", "user_role",
                       "user_role_description", "start_node_id", "opening_scene", "opening_line",
                       "difficulty", "estimated_duration"]:
            value = getattr(data, field, None)
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(value)
        
        for field in ["world_rules", "character_setting", "emotion_gates", "triggers", "tags"]:
            value = getattr(data, field, None)
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(json.dumps(value))
        
        if data.slug is not None:
            updates.append("slug = ?")
            params.append(data.slug)
        if data.is_public is not None:
            updates.append("is_public = ?")
            params.append(1 if data.is_public else 0)
        if data.status is not None:
            updates.append("status = ?")
            params.append(data.status.value if isinstance(data.status, ScriptStatus) else data.status)
        
        if not updates:
            return existing
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(script_id)
        
        await db.execute(
            f"UPDATE scripts SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        
        return await self.get_script(script_id)
    
    async def delete_script(self, script_id: str) -> bool:
        existing = await self.get_script(script_id)
        if not existing:
            return False
        
        await db.execute("DELETE FROM script_nodes WHERE script_id = ?", (script_id,))
        await db.execute("DELETE FROM scripts WHERE id = ?", (script_id,))
        
        logger.info(f"Deleted script: {script_id}")
        return True
    
    async def get_node(self, node_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM script_nodes WHERE id = ?",
            (node_id,),
            fetch=True
        )
        return self._node_row_to_dict(row) if row else None
    
    async def list_nodes(self, script_id: str) -> list[dict]:
        rows = await db.execute(
            "SELECT * FROM script_nodes WHERE script_id = ? ORDER BY position_y, position_x",
            (script_id,),
            fetch_all=True
        )
        return [self._node_row_to_dict(row) for row in rows]
    
    async def create_node(self, data: ScriptNodeCreate) -> dict:
        node_id = generate_node_id()
        
        await db.execute(
            """INSERT INTO script_nodes
               (id, script_id, node_type, title, description, narrative, character_inner_state,
                choices, effects, triggers, media_cue, prerequisites, emotion_gate, position_x, position_y, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                node_id,
                data.script_id,
                data.node_type.value if hasattr(data.node_type, 'value') else data.node_type,
                data.title,
                data.description,
                data.narrative,
                data.character_inner_state,
                json.dumps(data.choices) if data.choices else None,
                json.dumps(data.effects) if data.effects else None,
                json.dumps(data.triggers) if data.triggers else None,
                json.dumps(data.media_cue) if data.media_cue else None,
                json.dumps(data.prerequisites) if data.prerequisites else None,
                json.dumps(data.emotion_gate) if data.emotion_gate else None,
                0,
                0,
                datetime.utcnow().isoformat(),
            )
        )
        
        return await self.get_node(node_id)
    
    async def update_node(self, node_id: str, data: ScriptNodeUpdate) -> Optional[dict]:
        existing = await self.get_node(node_id)
        if not existing:
            return None
        
        updates = []
        params = []
        
        for field in ["node_type", "title", "description", "narrative", "character_inner_state",
                       "position_x", "position_y"]:
            value = getattr(data, field, None)
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(value.value if hasattr(value, 'value') else value)
        
        for field in ["choices", "effects", "triggers", "media_cue", "prerequisites", "emotion_gate"]:
            value = getattr(data, field, None)
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(json.dumps(value))
        
        if not updates:
            return existing
        
        params.append(node_id)
        
        await db.execute(
            f"UPDATE script_nodes SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        
        return await self.get_node(node_id)
    
    async def delete_node(self, node_id: str) -> bool:
        existing = await self.get_node(node_id)
        if not existing:
            return False
        
        await db.execute("DELETE FROM script_nodes WHERE id = ?", (node_id,))
        return True
    
    async def get_session_script_state(self, session_id: str) -> Optional[dict]:
        session = await db.execute(
            "SELECT script_id, script_state, script_node_id, quest_progress, context FROM chat_sessions WHERE id = ?",
            (session_id,),
            fetch=True
        )
        
        if not session or not session.get("script_id"):
            return None
        
        return {
            "script_id": session.get("script_id"),
            "state": session.get("script_state"),
            "current_node_id": session.get("script_node_id"),
            "quest_progress": session.get("quest_progress", 0),
            "variables": json.loads(session.get("context") or "{}"),
        }
    
    async def update_session_script_state(
        self,
        session_id: str,
        script_state: Optional[str] = None,
        node_id: Optional[str] = None,
        quest_progress: Optional[float] = None,
    ) -> bool:
        updates = ["updated_at = ?"]
        params = [datetime.utcnow().isoformat()]
        
        if script_state is not None:
            updates.append("script_state = ?")
            params.append(script_state)
        if node_id is not None:
            updates.append("script_node_id = ?")
            params.append(node_id)
        if quest_progress is not None:
            updates.append("quest_progress = ?")
            params.append(quest_progress)
        
        params.append(session_id)
        
        await db.execute(
            f"UPDATE chat_sessions SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        
        return True
    
    def _row_to_dict(self, row: dict) -> dict:
        result = dict(row)
        for field in ["world_rules", "character_setting", "emotion_gates", "triggers", "tags"]:
            if result.get(field) and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    pass
        for bool_field in ["is_public", "is_official"]:
            if bool_field in result:
                result[bool_field] = bool(result[bool_field])
        return result
    
    def _node_row_to_dict(self, row: dict) -> dict:
        result = dict(row)
        for field in ["choices", "effects", "triggers", "media_cue", "prerequisites", "emotion_gate"]:
            if result.get(field) and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    pass
        return result
    
    async def get_review(self, review_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM script_reviews WHERE id = ?",
            (review_id,),
            fetch=True
        )
        return dict(row) if row else None
    
    async def list_reviews(self, script_id: str) -> list[dict]:
        rows = await db.execute(
            "SELECT * FROM script_reviews WHERE script_id = ? ORDER BY created_at DESC",
            (script_id,),
            fetch_all=True
        )
        return [dict(row) for row in rows]
    
    async def list_pending_reviews(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[dict], int]:
        count_row = await db.execute(
            "SELECT COUNT(*) as cnt FROM scripts WHERE status = 'pending' AND is_official = 1",
            fetch=True
        )
        total = count_row.get("cnt", 0) if count_row else 0
        
        offset = (page - 1) * page_size
        rows = await db.execute(
            """SELECT s.*, c.name as character_name 
               FROM scripts s 
               LEFT JOIN characters c ON s.character_id = c.id
               WHERE s.status = 'pending' AND s.is_official = 1 
               ORDER BY s.updated_at DESC 
               LIMIT ? OFFSET ?""",
            (page_size, offset),
            fetch_all=True
        )
        scripts = [self._row_to_dict(row) for row in rows]
        return scripts, total
    
    async def submit_for_review(
        self,
        script_id: str,
        reviewer_id: str,
        comment: Optional[str] = None
    ) -> Optional[dict]:
        script = await self.get_script(script_id)
        if not script:
            return None
        
        if script.get("status") != ScriptStatus.DRAFT.value:
            return None
        
        review_id = generate_review_id()
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """INSERT INTO script_reviews (id, script_id, reviewer_id, action, previous_status, comment, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (review_id, script_id, reviewer_id, ReviewAction.SUBMIT.value, script.get("status"), comment, now)
        )
        
        await db.execute(
            "UPDATE scripts SET status = ?, updated_at = ? WHERE id = ?",
            (ScriptStatus.PUBLISHED.value if script.get("is_official") != 1 else "pending", now, script_id)
        )
        
        if script.get("is_official") == 1:
            await db.execute(
                "UPDATE scripts SET status = 'pending', updated_at = ? WHERE id = ?",
                (now, script_id)
            )
        
        return await self.get_review(review_id)
    
    async def approve_script(
        self,
        script_id: str,
        reviewer_id: str,
        comment: Optional[str] = None
    ) -> Optional[dict]:
        script = await self.get_script(script_id)
        if not script:
            return None
        
        if script.get("status") != "pending":
            return None
        
        review_id = generate_review_id()
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """INSERT INTO script_reviews (id, script_id, reviewer_id, action, previous_status, comment, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (review_id, script_id, reviewer_id, ReviewAction.APPROVE.value, script.get("status"), comment, now)
        )
        
        await db.execute(
            "UPDATE scripts SET status = ?, updated_at = ? WHERE id = ?",
            (ScriptStatus.PUBLISHED.value, now, script_id)
        )
        
        return await self.get_review(review_id)
    
    async def reject_script(
        self,
        script_id: str,
        reviewer_id: str,
        comment: Optional[str] = None
    ) -> Optional[dict]:
        script = await self.get_script(script_id)
        if not script:
            return None
        
        if script.get("status") != "pending":
            return None
        
        review_id = generate_review_id()
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """INSERT INTO script_reviews (id, script_id, reviewer_id, action, previous_status, comment, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (review_id, script_id, reviewer_id, ReviewAction.REJECT.value, script.get("status"), comment, now)
        )
        
        await db.execute(
            "UPDATE scripts SET status = ?, updated_at = ? WHERE id = ?",
            (ScriptStatus.DRAFT.value, now, script_id)
        )
        
        return await self.get_review(review_id)
    
    async def get_play_history(
        self,
        user_id: str,
        story_id: str
    ) -> list[dict]:
        rows = await db.execute(
            """SELECT id as play_id, play_index, status, ending_type, 
                      completion_time_minutes, started_at, completed_at,
                      (SELECT COUNT(*) FROM json_each(choices_made)) as choices_count
               FROM story_progress 
               WHERE user_id = ? AND story_id = ?
               ORDER BY play_index DESC""",
            (user_id, story_id),
            fetch_all=True
        )
        return [dict(row) for row in rows]
    
    async def get_all_user_play_history(
        self,
        user_id: str,
        character_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[dict], int]:
        conditions = ["user_id = ?"]
        params = [user_id]
        
        if character_id:
            conditions.append("character_id = ?")
            params.append(character_id)
        
        count_query = f"SELECT COUNT(*) as cnt FROM story_progress WHERE {' AND '.join(conditions)}"
        count_row = await db.execute(count_query, tuple(params), fetch=True)
        total = count_row.get("cnt", 0) if count_row else 0
        
        offset = (page - 1) * page_size
        query = f"""SELECT sp.*, s.title as story_title, c.name as character_name
                    FROM story_progress sp
                    LEFT JOIN scripts s ON sp.story_id = s.id
                    LEFT JOIN characters c ON sp.character_id = c.id
                    WHERE {' AND '.join(conditions)}
                    ORDER BY sp.last_played_at DESC
                    LIMIT ? OFFSET ?"""
        params.extend([page_size, offset])
        
        rows = await db.execute(query, tuple(params), fetch_all=True)
        return [dict(row) for row in rows], total
    
    async def increment_play_count(self, story_id: str) -> None:
        await db.execute(
            "UPDATE scripts SET play_count = play_count + 1, total_plays = COALESCE(total_plays, 0) + 1 WHERE id = ?",
            (story_id,)
        )
    
    async def get_next_play_index(self, user_id: str, story_id: str) -> int:
        row = await db.execute(
            "SELECT MAX(play_index) as max_idx FROM story_progress WHERE user_id = ? AND story_id = ?",
            (user_id, story_id),
            fetch=True
        )
        return (row.get("max_idx") or 0) + 1 if row else 1


script_service = ScriptService.get_instance()
