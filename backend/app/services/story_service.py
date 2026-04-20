import logging
from typing import Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from app.core.database import db

logger = logging.getLogger(__name__)


class EndingType(str, Enum):
    GOOD = "good"
    NEUTRAL = "neutral"
    BAD = "bad"
    SECRET = "secret"


class StoryStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


@dataclass
class EndingResult:
    is_ending: bool
    ending_type: Optional[str] = None
    rewards: Optional[dict] = None
    completion_time_minutes: int = 0
    narrative: Optional[str] = None


class StoryService:
    _instance = None

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls) -> "StoryService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def get_story(self, story_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM stories WHERE id = ?",
            (story_id,),
            fetch=True
        )
        return dict(row) if row else None

    async def get_story_node(self, node_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM story_nodes WHERE id = ?",
            (node_id,),
            fetch=True
        )
        if not row:
            return None
        result = dict(row)
        for field in ["choices", "character_context", "auto_advance", "trigger_conditions"]:
            import json
            if result.get(field) and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    pass
        return result

    async def get_progress(
        self,
        user_id: str,
        story_id: str
    ) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM story_progress WHERE user_id = ? AND story_id = ?",
            (user_id, story_id),
            fetch=True
        )
        if not row:
            return None
        result = dict(row)
        import json
        for field in ["visited_nodes", "choices_made"]:
            if result.get(field) and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    pass
        return result

    async def create_progress(
        self,
        user_id: str,
        story_id: str,
        character_id: str,
        start_node_id: str
    ) -> dict:
        import uuid
        progress_id = f"prog_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()

        await db.execute(
            """INSERT INTO story_progress
               (id, user_id, story_id, character_id, status, current_node_id,
                visited_nodes, choices_made, started_at, last_played_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                progress_id,
                user_id,
                story_id,
                character_id,
                StoryStatus.IN_PROGRESS.value,
                start_node_id,
                '["' + start_node_id + '"]',
                '[]',
                now,
                now
            )
        )

        return await self.get_progress(user_id, story_id)

    async def update_progress(
        self,
        progress_id: str,
        node_id: Optional[str] = None,
        choice_made: Optional[dict] = None,
        status: Optional[str] = None
    ) -> Optional[dict]:
        import json

        progress = await db.execute(
            "SELECT * FROM story_progress WHERE id = ?",
            (progress_id,),
            fetch=True
        )
        if not progress:
            return None

        updates = ["last_played_at = ?"]
        params = [datetime.utcnow().isoformat()]

        if node_id:
            updates.append("current_node_id = ?")
            params.append(node_id)

            visited = json.loads(progress.get("visited_nodes", "[]"))
            if node_id not in visited:
                visited.append(node_id)
            updates.append("visited_nodes = ?")
            params.append(json.dumps(visited))

        if choice_made:
            choices = json.loads(progress.get("choices_made", "[]"))
            choices.append(choice_made)
            updates.append("choices_made = ?")
            params.append(json.dumps(choices))

        if status:
            updates.append("status = ?")
            params.append(status)
            if status == StoryStatus.COMPLETED.value:
                updates.append("completed_at = ?")
                params.append(datetime.utcnow().isoformat())

        params.append(progress_id)

        await db.execute(
            f"UPDATE story_progress SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )

        return await db.execute(
            "SELECT * FROM story_progress WHERE id = ?",
            (progress_id,),
            fetch=True
        )

    async def determine_ending(
        self,
        progress_id: str
    ) -> EndingResult:
        progress = await db.execute(
            "SELECT * FROM story_progress WHERE id = ?",
            (progress_id,),
            fetch=True
        )
        if not progress:
            return EndingResult(is_ending=False)

        current_node_id = progress.get("current_node_id")
        if not current_node_id:
            return EndingResult(is_ending=False)

        node = await self.get_story_node(current_node_id)
        if not node:
            return EndingResult(is_ending=False)

        if not node.get("is_ending_node"):
            return EndingResult(is_ending=False)

        ending_type = node.get("ending_type", EndingType.NEUTRAL.value)
        narrative = node.get("scene_description")

        rewards = await self._calculate_rewards(progress, node)

        started_at = progress.get("started_at")
        completion_time = 0
        if started_at:
            try:
                start = datetime.fromisoformat(started_at)
                end = datetime.utcnow()
                completion_time = int((end - start).total_seconds() / 60)
            except Exception:
                pass

        await self.update_progress(
            progress_id,
            status=StoryStatus.COMPLETED.value
        )

        return EndingResult(
            is_ending=True,
            ending_type=ending_type,
            rewards=rewards,
            completion_time_minutes=completion_time,
            narrative=narrative
        )

    async def _calculate_rewards(
        self,
        progress: dict,
        ending_node: dict
    ) -> dict:
        import json

        base_rewards = {
            "trust_bonus": 0,
            "intimacy_bonus": 0,
            "unlock_story_ids": []
        }

        ending_type = ending_node.get("ending_type", EndingType.NEUTRAL.value)

        type_bonuses = {
            EndingType.GOOD.value: {"trust_bonus": 10, "intimacy_bonus": 15},
            EndingType.NEUTRAL.value: {"trust_bonus": 5, "intimacy_bonus": 5},
            EndingType.BAD.value: {"trust_bonus": 0, "intimacy_bonus": 0},
            EndingType.SECRET.value: {"trust_bonus": 15, "intimacy_bonus": 20}
        }

        base_rewards.update(type_bonuses.get(ending_type, {}))

        choices_made = json.loads(progress.get("choices_made", "[]"))
        for choice in choices_made:
            effects = choice.get("effects", {})
            base_rewards["trust_bonus"] += effects.get("trust_delta", 0)
            base_rewards["intimacy_bonus"] += effects.get("intimacy_delta", 0)

        base_rewards["trust_bonus"] = max(0, min(30, base_rewards["trust_bonus"]))
        base_rewards["intimacy_bonus"] = max(0, min(30, base_rewards["intimacy_bonus"]))

        return base_rewards

    async def get_possible_endings(
        self,
        story_id: str,
        visited_nodes: Optional[list[str]] = None
    ) -> list[dict]:
        rows = await db.execute(
            "SELECT id, title, ending_type, scene_description FROM story_nodes WHERE story_id = ? AND is_ending_node = 1",
            (story_id,),
            fetch_all=True
        )

        endings = []
        for row in rows:
            ending = dict(row)
            ending["reachable"] = True
            endings.append(ending)

        return endings


story_service = StoryService()
