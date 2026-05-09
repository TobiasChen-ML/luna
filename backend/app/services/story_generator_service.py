"""
Story Generator Service

Converts a chat session's conversation history into an interactive branching
story stored in the scripts / script_nodes tables.
"""

import asyncio
import json
import logging
import uuid
from typing import Optional

from app.core.database import db
from app.services.llm_service import LLMService
from app.services.script_service import script_service
from app.services.chat_history_service import chat_history_service
from app.models.script import ScriptCreate, ScriptNodeCreate, ScriptNodeType

logger = logging.getLogger(__name__)

STORY_SCHEMA = {
    "type": "object",
    "required": ["title", "summary", "cover_prompt", "genre", "opening_line", "opening_scene", "nodes"],
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "cover_prompt": {"type": "string", "description": "Image generation prompt for the story cover"},
        "genre": {"type": "string"},
        "opening_line": {"type": "string"},
        "opening_scene": {"type": "string"},
        "nodes": {
            "type": "array",
            "minItems": 3,
            "maxItems": 8,
            "items": {
                "type": "object",
                "required": ["type", "title", "narrative"],
                "properties": {
                    "type": {"type": "string", "enum": ["scene", "ending"]},
                    "title": {"type": "string"},
                    "narrative": {"type": "string"},
                    "choices": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "maxItems": 3,
                    },
                },
            },
        },
    },
}

_SYSTEM_PROMPT = """You are a creative interactive fiction writer. Given a conversation between a user and an AI character, create an engaging branching story that captures the emotional highlights and relationship dynamics.

Rules:
- The story should feel personal and intimate, reflecting the actual conversation themes
- Scene nodes must include 2-3 short, vivid choices for the reader
- Ending nodes have no choices
- Keep narrative text under 150 words per node
- Cover prompt should be a Stable Diffusion prompt describing the key visual mood
- Write in second person ("You...")
- Return ONLY valid JSON matching the schema"""


def _build_story_prompt(
    messages: list[dict],
    character_name: str,
    relationship_stage: str,
) -> str:
    history_lines = []
    for m in messages[-40:]:
        role = "You" if m.get("role") == "user" else character_name
        content = (m.get("content") or "").strip()
        if content:
            history_lines.append(f"{role}: {content}")

    history_text = "\n".join(history_lines)

    return (
        f"Conversation between the user and {character_name} "
        f"(relationship stage: {relationship_stage}):\n\n"
        f"{history_text}\n\n"
        "Transform this conversation into an interactive branching story with 4-6 scene nodes "
        "and 1-2 ending nodes. The story should dramatize the emotional arc of this relationship."
    )


async def generate_story_from_session(
    session_id: str,
    user_id: str,
    character_id: str,
    script_id: Optional[str] = None,
) -> Optional[str]:
    """
    Generate an interactive story from a chat session and save it to the DB.
    Returns the script_id on success, None on failure.
    """
    try:
        messages = await chat_history_service.get_recent_messages(session_id, limit=50)
        if len(messages) < 6:
            logger.warning(f"Session {session_id} has too few messages for story generation")
            return None

        from app.services.character_service import character_service
        from app.services.relationship_service import relationship_service

        character = await character_service.get_character_by_id(character_id)
        character_name = (
            (character or {}).get("first_name")
            or (character or {}).get("name")
            or "AI"
        )

        rel = await relationship_service.get_relationship(user_id, character_id)
        relationship_stage = (rel or {}).get("stage", "stranger")

        llm = LLMService.get_instance()
        story_prompt = _build_story_prompt(messages, character_name, relationship_stage)

        structured = await llm.generate_structured(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": story_prompt},
            ],
            schema=STORY_SCHEMA,
            temperature=0.7,
        )

        story_data = structured.data
        if not story_data or not story_data.get("nodes"):
            logger.error(f"LLM returned empty story data for session {session_id}")
            return None

        script = await script_service.create_script(
            ScriptCreate(
                title=story_data["title"],
                genre=story_data.get("genre", "romance"),
                world_setting=story_data.get("summary", ""),
                opening_scene=story_data.get("opening_scene", ""),
                opening_line=story_data.get("opening_line", ""),
                character_role="companion",
                tags=["generated", "from_chat"],
                character_id=character_id,
            ),
            script_id=script_id,
        )
        script_id = script["id"]

        await db.execute(
            "UPDATE scripts SET source_session_id = ?, is_public = 0 WHERE id = ?",
            (session_id, script_id),
        )

        nodes = story_data.get("nodes", [])
        first_node_id = None

        for i, node_data in enumerate(nodes):
            node_type_str = node_data.get("type", "scene")
            node_type = (
                ScriptNodeType.ENDING
                if node_type_str == "ending"
                else ScriptNodeType.SCENE
            )

            choices_raw = node_data.get("choices") or []
            choices_payload = (
                [{"text": c, "id": f"choice_{uuid.uuid4().hex[:8]}"} for c in choices_raw]
                if choices_raw and node_type != ScriptNodeType.ENDING
                else None
            )

            node = await script_service.create_node(
                ScriptNodeCreate(
                    script_id=script_id,
                    node_type=node_type,
                    title=node_data.get("title", f"Scene {i + 1}"),
                    narrative=node_data.get("narrative", ""),
                    choices=choices_payload,
                )
            )

            if i == 0:
                first_node_id = node["id"]

        if first_node_id:
            await db.execute(
                "UPDATE scripts SET start_node_id = ? WHERE id = ?",
                (first_node_id, script_id),
            )

        asyncio.create_task(
            _generate_story_cover(
                script_id=script_id,
                cover_prompt=story_data.get("cover_prompt", f"cinematic scene, {character_name}, romantic atmosphere"),
                character=character,
            )
        )

        from app.services.milestone_service import write_milestone
        asyncio.create_task(
            write_milestone(
                user_id=user_id,
                character_id=character_id,
                milestone_type="story_created",
                description=f"Created story: {story_data['title']}",
            )
        )

        logger.info(f"Generated story {script_id} from session {session_id} ({len(nodes)} nodes)")
        return script_id

    except Exception as e:
        logger.error(f"Story generation failed for session {session_id}: {e}", exc_info=True)
        return None


async def _generate_story_cover(
    script_id: str,
    cover_prompt: str,
    character: Optional[dict],
) -> None:
    try:
        from app.services.media_service import MediaService

        media_service = MediaService.get_instance()
        image_provider = media_service.get_image_provider()

        avatar_url = (
            (character or {}).get("profile_image_url")
            or (character or {}).get("avatar_url")
            or (character or {}).get("cover_url")
        )

        if avatar_url:
            import httpx
            import base64
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(avatar_url)
                if resp.status_code == 200:
                    avatar_b64 = base64.b64encode(resp.content).decode()
                    from app.services.media import IPAdapterConfig
                    task_id = await image_provider.txt2img_async(
                        prompt=f"{cover_prompt}, story cover art, cinematic lighting",
                        negative_prompt="low quality, blurry, text, watermark",
                        width=768,
                        height=432,
                        ip_adapters=[IPAdapterConfig(image_base64=avatar_b64, strength=0.35)],
                    )
                else:
                    raise ValueError("avatar fetch failed")
        else:
            task_id = await image_provider.txt2img_async(
                prompt=f"{cover_prompt}, story cover art, cinematic lighting",
                negative_prompt="low quality, blurry, text, watermark",
                width=768,
                height=432,
            )

        result = await image_provider.wait_for_task(task_id, timeout_seconds=120)
        if result.image_url:
            await db.execute(
                "UPDATE scripts SET cover_image_url = ? WHERE id = ?",
                (result.image_url, script_id),
            )
            logger.info(f"Story cover generated for {script_id}: {result.image_url}")
    except Exception as e:
        logger.warning(f"Story cover generation failed for {script_id}: {e}")
