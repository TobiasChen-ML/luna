import logging
from typing import Optional, Any
from datetime import datetime

from app.core.database import db
from app.services.media_service import MediaService

logger = logging.getLogger(__name__)


class MediaTriggerService:
    _instance = None

    def __init__(self):
        self._generation_tasks: dict[str, dict] = {}

    @classmethod
    def get_instance(cls) -> "MediaTriggerService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def can_trigger(
        self,
        script_id: str,
        node_id: str,
        cue_id: str,
        session_id: str,
        relationship_state: Optional[dict] = None
    ) -> dict[str, Any]:
        node = await db.execute(
            "SELECT * FROM script_nodes WHERE id = ? AND script_id = ?",
            (node_id, script_id),
            fetch=True
        )

        if not node:
            return {"allowed": False, "reason": "node_not_found"}

        import json
        media_cue = None
        if node.get("media_cue"):
            try:
                media_cue = json.loads(node["media_cue"])
            except json.JSONDecodeError:
                pass

        if not media_cue:
            return {"allowed": False, "reason": "no_media_cue"}

        if media_cue.get("cue_id") != cue_id:
            return {"allowed": False, "reason": "cue_id_mismatch"}

        session = await db.execute(
            "SELECT script_id, script_node_id, quest_progress, context FROM chat_sessions WHERE id = ?",
            (session_id,),
            fetch=True
        )

        if not session:
            return {"allowed": False, "reason": "session_not_found"}

        triggered_key = f"triggered_cues:{session_id}"
        triggered_cues = await self._get_triggered_cues(session_id)
        if cue_id in triggered_cues:
            return {"allowed": False, "reason": "already_triggered"}

        min_intimacy = media_cue.get("min_intimacy", 0)
        if relationship_state:
            current_intimacy = relationship_state.get("intimacy", 0)
            if current_intimacy < min_intimacy:
                return {
                    "allowed": False,
                    "reason": "insufficient_intimacy",
                    "current": current_intimacy,
                    "required": min_intimacy
                }

        return {
            "allowed": True,
            "media_cue": media_cue
        }

    async def trigger_media(
        self,
        script_id: str,
        node_id: str,
        cue_id: str,
        session_id: str,
        user_id: str,
        character_id: str
    ) -> dict[str, Any]:
        can_trigger_result = await self.can_trigger(
            script_id, node_id, cue_id, session_id
        )

        if not can_trigger_result.get("allowed"):
            return can_trigger_result

        media_cue = can_trigger_result["media_cue"]
        media_type = media_cue.get("type", "image")
        prompt = media_cue.get("prompt", "")

        if not prompt:
            return {"allowed": False, "reason": "no_prompt"}

        try:
            media_service = MediaService.get_instance()

            task_id = f"media_{cue_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            self._generation_tasks[task_id] = {
                "status": "pending",
                "type": media_type,
                "cue_id": cue_id,
                "created_at": datetime.utcnow().isoformat()
            }

            if media_type == "image":
                result = await media_service.generate_image(
                    prompt=prompt,
                    width=512,
                    height=768
                )
                self._generation_tasks[task_id]["status"] = "completed"
                self._generation_tasks[task_id]["result"] = result

                await self._mark_cue_triggered(session_id, cue_id)

                return {
                    "allowed": True,
                    "task_id": task_id,
                    "media_type": media_type,
                    "image_url": result.get("url"),
                    "estimated_seconds": 15
                }

            elif media_type == "video":
                result = await media_service.generate_video(
                    prompt=prompt
                )
                self._generation_tasks[task_id]["status"] = "completed"
                self._generation_tasks[task_id]["result"] = result

                await self._mark_cue_triggered(session_id, cue_id)

                return {
                    "allowed": True,
                    "task_id": task_id,
                    "media_type": media_type,
                    "video_url": result.get("url"),
                    "estimated_seconds": 30
                }

            else:
                return {"allowed": False, "reason": "unsupported_media_type"}

        except Exception as e:
            logger.error(f"Media generation failed: {e}")
            return {
                "allowed": False,
                "reason": "generation_failed",
                "error": str(e)
            }

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        return self._generation_tasks.get(task_id)

    async def _get_triggered_cues(self, session_id: str) -> list[str]:
        session = await db.execute(
            "SELECT context FROM chat_sessions WHERE id = ?",
            (session_id,),
            fetch=True
        )

        if not session:
            return []

        import json
        context = {}
        if session.get("context"):
            try:
                context = json.loads(session["context"])
            except json.JSONDecodeError:
                pass

        return context.get("triggered_media_cues", [])

    async def _mark_cue_triggered(self, session_id: str, cue_id: str):
        session = await db.execute(
            "SELECT context FROM chat_sessions WHERE id = ?",
            (session_id,),
            fetch=True
        )

        import json
        context = {}
        if session and session.get("context"):
            try:
                context = json.loads(session["context"])
            except json.JSONDecodeError:
                pass

        triggered = context.get("triggered_media_cues", [])
        if cue_id not in triggered:
            triggered.append(cue_id)

        context["triggered_media_cues"] = triggered

        await db.execute(
            "UPDATE chat_sessions SET context = ? WHERE id = ?",
            (json.dumps(context), session_id)
        )


media_trigger_service = MediaTriggerService()
