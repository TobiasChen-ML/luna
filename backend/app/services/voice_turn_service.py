import logging
from dataclasses import dataclass
from typing import Optional

from .voice_service import VoiceService
from .llm_service import LLMService
from .credit_service import CreditService, InsufficientCreditsError
from .chat_history_service import chat_history_service
from .character_service import character_service
from .relationship_service import relationship_service
from .redis_service import RedisService
from .emotion_voice_mapper import parse_emotion_tag
from .prompt_builder import PromptBuilder, PromptContext, PromptSection
from ..models import ChatMessageCreate
from ..models.chat_session import MessageType

logger = logging.getLogger(__name__)

_CREDITS_PER_MINUTE = 3.0
_SESSION_DURATION_KEY = "voice_turn_session:{session_id}:duration"

VOICE_MODE_INSTRUCTION = """
## Voice Mode
You are responding via voice. Prepend your reply with an emotion tag on the same line:
[emotion:撒娇] / [emotion:开心] / [emotion:兴奋] / [emotion:生气] / [emotion:委屈] /
[emotion:害羞] / [emotion:悲伤] / [emotion:温柔] / [emotion:平静] / [emotion:惊讶] /
[emotion:担心] / [emotion:调皮]

Choose the tag that best matches the feeling of your reply.
After the tag write your response as normal — no other format changes.
Do NOT use Markdown bold/italic/blockquotes; plain spoken text only.
Keep the reply concise (1–3 sentences) since it will be read aloud.
"""


@dataclass
class VoiceTurnResult:
    audio_bytes: bytes
    transcript_in: str
    transcript_out: str
    emotion: str
    credits_used: float
    session_total_seconds: float


class VoiceTurnService:
    def __init__(
        self,
        voice_service: Optional[VoiceService] = None,
        llm_service: Optional[LLMService] = None,
        credit_service: Optional[CreditService] = None,
        redis: Optional[RedisService] = None,
    ):
        self.voice = voice_service or VoiceService()
        self.llm = llm_service or LLMService.get_instance()
        self.credits = credit_service or CreditService()
        self.redis = redis or RedisService()
        self.prompt_builder = PromptBuilder.get_instance()

    async def check_credits(self, user_id: str) -> bool:
        balance = await self.credits.get_balance(user_id)
        return balance.get("total", 0) >= _CREDITS_PER_MINUTE / 60

    async def process_turn(
        self,
        audio_bytes: bytes,
        session_id: str,
        character_id: str,
        user_id: str,
        input_duration_seconds: float = 0.0,
        language: str = "zh",
    ) -> VoiceTurnResult:
        balance = await self.credits.get_balance(user_id)
        if balance.get("total", 0) < _CREDITS_PER_MINUTE / 60:
            raise InsufficientCreditsError("Insufficient credits for voice turn")

        # STT
        transcript_in = await self.voice.speech_to_text(audio_bytes, language=language)
        if not transcript_in.strip():
            raise ValueError("Could not transcribe audio")

        # Build prompt context (character + relationship + memory + history)
        ctx, character = await self._build_context(character_id, user_id, session_id)
        messages = await self.prompt_builder.build_messages(ctx, transcript_in)

        # Inject voice mode instruction into system prompt
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] += VOICE_MODE_INSTRUCTION

        # LLM
        response = await self.llm.generate(messages, max_tokens=300, temperature=0.75)
        raw_text = response.content if hasattr(response, "content") else str(response)

        emotion, clean_text = parse_emotion_tag(raw_text)
        if not emotion:
            emotion = "default"

        voice_id = (character or {}).get("voice_id") or "Rachel"

        # TTS — collect streamed bytes
        audio_chunks: list[bytes] = []
        async for chunk in self.voice.stream_tts(clean_text, voice_id=voice_id, emotion=emotion):
            audio_chunks.append(chunk)
        audio_bytes_out = b"".join(audio_chunks)

        # Credit deduction: input duration + estimated TTS duration (MP3 128kbps)
        tts_duration = len(audio_bytes_out) * 8 / 128_000
        total_seconds = input_duration_seconds + tts_duration
        credits_used = (total_seconds / 60) * _CREDITS_PER_MINUTE

        try:
            await self.credits.deduct_credits(
                user_id=user_id,
                amount=round(credits_used, 4),
                usage_type="voice_turn",
                character_id=character_id,
                session_id=session_id,
                description=f"Voice turn: {total_seconds:.1f}s",
            )
        except InsufficientCreditsError:
            logger.warning(f"Credits ran out mid-turn for user={user_id}")

        # Persist both sides of the turn to chat history
        await self._save_turn(session_id, character_id, user_id, transcript_in, clean_text)

        # Accumulate session duration in Redis (for display)
        session_key = _SESSION_DURATION_KEY.format(session_id=session_id)
        prior = await self.redis.get_json(session_key) or 0.0
        await self.redis.set_json(session_key, prior + total_seconds, ex=86400)

        return VoiceTurnResult(
            audio_bytes=audio_bytes_out,
            transcript_in=transcript_in,
            transcript_out=clean_text,
            emotion=emotion,
            credits_used=round(credits_used, 4),
            session_total_seconds=prior + total_seconds,
        )

    async def _build_context(
        self,
        character_id: str,
        user_id: str,
        session_id: str,
    ) -> tuple[PromptContext, dict]:
        character = await character_service.get_character_by_id(character_id) or {}

        ctx = PromptContext(
            character_id=character_id,
            character_name=character.get("name", "AI"),
            character_age=int(character.get("age") or 0) or None,
            character_gender=character.get("gender", "female"),
            personality_summary=character.get("personality_summary"),
            personality_example=character.get("personality_example"),
            backstory=character.get("backstory"),
            response_length_hint="1–3 short spoken sentences",
            enabled_sections={
                PromptSection.CHARACTER_SETTING,
                PromptSection.RELATIONSHIP_STATE,
                PromptSection.MEMORY_CONTEXT,
                PromptSection.OUTPUT_INSTRUCTION,
            },
        )

        rel = await relationship_service.get_relationship(user_id, character_id)
        if rel:
            ctx.relationship_stage = rel.get("stage", "stranger")
            ctx.intimacy = rel.get("intimacy", 0)
            ctx.trust = rel.get("trust", 0)
            ctx.desire = rel.get("desire", 0)
            ctx.dependency = rel.get("dependency", 0)
            ctx.relationship_history_summary = rel.get("history_summary")

        try:
            from .memory_service import MemoryService
            if not hasattr(self, "_mem_svc"):
                self._mem_svc = MemoryService()
            memory_ctx = await self._mem_svc.get_context(character_id, user_id)
            if memory_ctx:
                ctx.episodic_memories = memory_ctx.get("episodic_memories", [])
                ctx.semantic_facts = memory_ctx.get("semantic_facts", [])
                ctx.recent_topics = memory_ctx.get("recent_topics", [])
        except Exception as e:
            logger.warning(f"Memory context unavailable: {e}")

        recent = await chat_history_service.get_recent_messages(session_id, limit=10)
        ctx.conversation_history = [
            {"role": m["role"], "content": m["content"]} for m in recent
        ]

        return ctx, character

    async def _save_turn(
        self,
        session_id: str,
        character_id: str,
        user_id: str,
        user_text: str,
        assistant_text: str,
    ) -> None:
        try:
            await chat_history_service.save_message(ChatMessageCreate(
                session_id=session_id,
                role="user",
                content=user_text,
                character_id=character_id,
                user_id=user_id,
                message_type=MessageType.VOICE_NOTE,
            ))
            await chat_history_service.save_message(ChatMessageCreate(
                session_id=session_id,
                role="assistant",
                content=assistant_text,
                character_id=character_id,
                user_id=user_id,
                message_type=MessageType.VOICE_NOTE,
            ))
        except Exception as e:
            logger.warning(f"Failed to save voice turn to history: {e}")


voice_turn_service = VoiceTurnService()
