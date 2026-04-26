import logging
from dataclasses import dataclass
from typing import Any, Optional, Literal

from app.services.image_intent_handler import (
    detect_image_intent_keywords,
    image_intent_handler,
)
from app.services.intent_detector import detect_video_intent_keywords

logger = logging.getLogger(__name__)


ToolName = Literal["chat", "generate_image", "generate_video", "generate_voice"]


@dataclass
class CharacterToolPlan:
    tool_name: ToolName
    confidence: float = 0.0
    prompt: Optional[str] = None
    reason: str = ""

    @property
    def uses_media_tool(self) -> bool:
        return self.tool_name in {"generate_image", "generate_video"}


@dataclass
class CharacterToolResult:
    tool_name: ToolName
    task_id: Optional[str] = None
    response_message: Optional[str] = None
    prompt: Optional[str] = None
    error: Optional[str] = None


class CharacterAgentOrchestrator:
    """Routes character-agent turns to text or media tools."""

    async def plan_tool(
        self,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
    ) -> CharacterToolPlan:
        message = (user_message or "").strip()
        if not message:
            return CharacterToolPlan("chat", reason="empty_message")

        image_detected, image_confidence = detect_image_intent_keywords(message)
        video_detected, video_confidence = detect_video_intent_keywords(message)

        try:
            intent = await llm_service.detect_intent(
                message,
                context={"character_name": character.get("name")},
            )
        except Exception as e:
            logger.debug("Agent tool intent detection failed: %s", e)
            intent = {}

        llm_intent = str(intent.get("intent") or "").lower()
        llm_confidence = float(intent.get("confidence") or 0.0)
        llm_action = str(intent.get("action") or intent.get("tool_hint") or "")

        if video_detected and video_confidence >= 0.5:
            return CharacterToolPlan(
                "generate_video",
                confidence=video_confidence,
                prompt=message,
                reason="video_keyword",
            )

        if llm_intent == "video" and llm_confidence >= 0.55:
            return CharacterToolPlan(
                "generate_video",
                confidence=llm_confidence,
                prompt=llm_action or message,
                reason="llm_intent",
            )

        if image_detected and image_confidence >= 0.5:
            return CharacterToolPlan(
                "generate_image",
                confidence=image_confidence,
                prompt=message,
                reason="image_keyword",
            )

        if llm_intent == "image" and llm_confidence >= 0.55:
            return CharacterToolPlan(
                "generate_image",
                confidence=llm_confidence,
                prompt=llm_action or message,
                reason="llm_intent",
            )

        if llm_intent == "audio" and llm_confidence >= 0.55:
            return CharacterToolPlan(
                "generate_voice",
                confidence=llm_confidence,
                reason="llm_intent",
            )

        return CharacterToolPlan("chat", confidence=llm_confidence, reason="default_chat")

    async def execute_media_tool(
        self,
        plan: CharacterToolPlan,
        *,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
        media_service: Any,
        session_id: Optional[str],
        user_id: Optional[str],
    ) -> CharacterToolResult:
        if plan.tool_name == "generate_image":
            return await self._generate_image(
                user_message=user_message,
                character=character,
                llm_service=llm_service,
                media_service=media_service,
                session_id=session_id,
                user_id=user_id,
            )
        if plan.tool_name == "generate_video":
            return await self._generate_video(
                user_message=user_message,
                character=character,
                llm_service=llm_service,
                media_service=media_service,
                session_id=session_id,
                user_id=user_id,
            )
        return CharacterToolResult(tool_name=plan.tool_name)

    async def _generate_image(
        self,
        *,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
        media_service: Any,
        session_id: Optional[str],
        user_id: Optional[str],
    ) -> CharacterToolResult:
        reference_image = self._character_reference_image(character)
        result = await image_intent_handler.handle_image_intent(
            user_message=user_message,
            character=character,
            llm_service=llm_service,
            media_service=media_service,
            session_id=session_id,
            character_image_url=reference_image,
        )

        task_id = result.get("task_id")
        if task_id:
            await self._cache_task_context(
                task_id=task_id,
                session_id=session_id,
                character_id=character.get("id"),
                user_id=user_id,
                media_type="image",
            )

        return CharacterToolResult(
            tool_name="generate_image",
            task_id=task_id,
            response_message=result.get("response_message"),
            prompt=result.get("prompt"),
            error=None if task_id else "image_generation_not_submitted",
        )

    async def _generate_video(
        self,
        *,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
        media_service: Any,
        session_id: Optional[str],
        user_id: Optional[str],
    ) -> CharacterToolResult:
        from app.services.media import NovitaVideoProvider

        provider = media_service.get_video_provider("novita")
        if not provider or not isinstance(provider, NovitaVideoProvider):
            return CharacterToolResult(
                tool_name="generate_video",
                response_message="I can't start the video tool right now. Try again in a moment.",
                error="video_provider_unavailable",
            )

        prompt = await self._extract_visual_prompt(user_message, character, llm_service)
        reference_image = self._character_reference_image(character)
        task_id = await provider.generate_video_async(
            prompt=prompt,
            init_image=reference_image,
        )
        await self._cache_task_context(
            task_id=task_id,
            session_id=session_id,
            character_id=character.get("id"),
            user_id=user_id,
            media_type="video",
        )

        return CharacterToolResult(
            tool_name="generate_video",
            task_id=task_id,
            response_message=await self._generate_accept_message(
                user_message,
                character,
                llm_service,
                media_type="video",
            ),
            prompt=prompt,
        )

    async def _extract_visual_prompt(
        self,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
    ) -> str:
        schema = {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
            },
            "required": ["prompt"],
        }
        system_prompt = (
            "Convert the user's request into a concise visual generation prompt. "
            "Keep the character identity, pose, clothing, action, setting, and mood. "
            "Return valid JSON only."
        )
        try:
            response = await llm_service.generate_structured(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Character: {character.get('name', 'the character')}\n"
                            f"Request: {user_message}"
                        ),
                    },
                ],
                schema=schema,
                temperature=0.2,
            )
            prompt = str(response.data.get("prompt") or "").strip()
            if prompt:
                return f"{character.get('name', 'the character')}, {prompt}"
        except Exception as e:
            logger.debug("Visual prompt extraction failed: %s", e)
        return f"{character.get('name', 'the character')}, {user_message}"

    async def _generate_accept_message(
        self,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
        *,
        media_type: str,
    ) -> str:
        personality = character.get("personality_summary") or "warm and natural"
        prompt = f"""The user asked the character to create a {media_type}.
The {media_type} is handled by an available system tool, so the character should not refuse because of job, identity, spirituality, or technology limitations.
Reply in character with a short natural acknowledgement, 1 sentence.

Character: {character.get('name', 'Assistant')}
Personality: {personality}
User request: {user_message}"""
        try:
            response = await llm_service.generate(
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7,
                max_tokens=80,
            )
            message = response.content.strip()
            if message:
                return message
        except Exception as e:
            logger.debug("Tool accept message generation failed: %s", e)
        return f"Of course. I'll make that {media_type} for you."

    def _character_reference_image(self, character: dict[str, Any]) -> Optional[str]:
        for key in (
            "mature_image_url",
            "mature_cover_url",
            "profile_image_url",
            "avatar_url",
            "cover_url",
        ):
            value = str(character.get(key) or "").strip()
            if value:
                return value
        return None

    async def _cache_task_context(
        self,
        *,
        task_id: Optional[str],
        session_id: Optional[str],
        character_id: Optional[str],
        user_id: Optional[str],
        media_type: str,
    ) -> None:
        if not task_id:
            return
        try:
            from app.routers.media import _cache_image_task_context

            await _cache_image_task_context(
                task_id=task_id,
                session_id=session_id,
                character_id=character_id,
                user_id=user_id,
                media_type=media_type,
            )
        except Exception as e:
            logger.warning("Failed to cache media task context: %s", e)


character_agent_orchestrator = CharacterAgentOrchestrator()
