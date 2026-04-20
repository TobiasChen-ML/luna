import json
import logging
import asyncio
import uuid
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any, Optional
from sse_starlette.sse import EventSourceResponse

from app.models import (
    BaseResponse, ChatStreamRequest, ChatCompleteRequest,
    ChatSession, ChatMessage, ChatMessageCreate as ChatMessageCreateModel
)
from app.core.events import EventType, SSEEvent
from app.core.dependencies import get_current_user_required
from app.services.llm_service import LLMService
from app.services.prompt_builder import PromptBuilder, PromptContext, PromptSection
from app.services.prompt_template_service import prompt_template_service
from app.services.character_service import character_service
from app.services.relationship_service import relationship_service
from app.services.relationship_analyzer import relationship_analyzer
from app.services.script_service import script_service
from app.services.chat_history_service import chat_history_service
from app.services.content_safety import content_safety
from app.services.video_intent_handler import video_intent_handler
from app.services.voice_service import VoiceService
from app.services.database_service import DatabaseService
from app.services.credit_service import credit_service
from app.services.pricing_service import pricing_service
from app.services.script_library_service import script_library_service

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)

VOICE_CREDIT_COST = 2
IMAGE_CREDIT_COST = 2


def _replace_script_placeholders(data: Any, character_name: str) -> Any:
    if isinstance(data, str):
        return data.replace("{{character_name}}", character_name)
    if isinstance(data, dict):
        return {k: _replace_script_placeholders(v, character_name) for k, v in data.items()}
    if isinstance(data, list):
        return [_replace_script_placeholders(item, character_name) for item in data]
    return data


def _get_user_id(request: Request) -> str:
    return getattr(request.state, "user_id", "guest")


def _get_user_db_id(request: Request) -> Optional[str]:
    return getattr(request.state, "user_db_id", None)


async def _build_prompt_context(
    character_id: str,
    user_id: str,
    session_id: Optional[str] = None,
    script_id: Optional[str] = None,
) -> PromptContext:
    character = await character_service.get_character_by_id(character_id)
    if not character:
        character = {"name": "Assistant", "gender": "female"}
    
    ctx = PromptContext(
        character_id=character_id,
        character_name=character.get("name", "Assistant"),
        character_age=int(character.get("age") or 0) if character.get("age") else None,
        character_gender=character.get("gender", "female"),
        personality_summary=character.get("personality_summary"),
        personality_example=character.get("personality_example"),
        backstory=character.get("backstory"),
    )
    
    rel = await relationship_service.get_relationship(user_id, character_id)
    if rel:
        ctx.relationship_stage = rel.get("stage", "stranger")
        ctx.intimacy = rel.get("intimacy", 0)
        ctx.trust = rel.get("trust", 0)
        ctx.desire = rel.get("desire", 0)
        ctx.dependency = rel.get("dependency", 0)
        ctx.relationship_history_summary = rel.get("history_summary")
        ctx.next_stage_requirements = relationship_service.get_next_stage_requirements(
            rel.get("stage", "stranger")
        )
    
    effective_script_id = script_id
    if session_id and not effective_script_id:
        session = await chat_history_service.get_session(session_id)
        if session:
            effective_script_id = session.get("script_id")
    
    if effective_script_id:
        if effective_script_id.startswith("ethical_") or effective_script_id.startswith("script_lib_"):
            script_lib = await script_library_service.get_script(effective_script_id)
            if script_lib:
                ctx.script_id = effective_script_id
                ctx.use_script_library = True
                
                seed = script_lib.script_seed
                full = script_lib.full_script
                
                ctx.script_library_seed = seed.model_dump() if seed else None

                if full:
                    full = _replace_script_placeholders(full, ctx.character_name)
                ctx.script_library_full = full
                
                if seed:
                    if seed.character:
                        if seed.character.age:
                            ctx.character_age = seed.character.age
                    if seed.contrast:
                        ctx.backstory = f"表面：{seed.contrast.surface}。真实：{seed.contrast.truth}。"
                    if seed.progression:
                        ctx.current_scene_description = seed.progression.start
                
                if full:
                    if full.get("prologue"):
                        ctx.backstory = full["prologue"]
                    if full.get("opening_scene"):
                        ctx.current_scene_description = full["opening_scene"]
                    if full.get("character_inner_state"):
                        state = full["character_inner_state"]
                        ctx.character_inner_state = state.get("initial", "")
                    if full.get("narrative_beats"):
                        beats = full["narrative_beats"]
                        if beats:
                            first_beat = beats[0]
                            ctx.current_scene_description = first_beat.get("scene", "")
                            ctx.narrative_context = first_beat.get("hint", "")
                
                ctx.world_setting = script_lib.summary
                ctx.character_role = script_lib.relation_types[0] if script_lib.relation_types else ""
                
                ctx.enabled_sections.add(PromptSection.SCRIPT_INSTRUCTION)
                ctx.enabled_sections.add(PromptSection.WORLD_SETTING)
                ctx.enabled_sections.add(PromptSection.PLOT_CONTEXT)
        else:
            script = await script_service.get_script(effective_script_id)
            if script:
                ctx.script_id = effective_script_id
                ctx.world_setting = script.get("world_setting")
                ctx.world_rules = script.get("world_rules") or []
                ctx.character_role = script.get("character_role")
                ctx.character_role_description = script.get("character_role_description")
                ctx.user_role = script.get("user_role")
                ctx.user_role_description = script.get("user_role_description")
                
                script_char_setting = script.get("character_setting") or {}
                if script_char_setting.get("backstory"):
                    ctx.backstory = script_char_setting["backstory"]
                if script_char_setting.get("personality_summary"):
                    ctx.personality_summary = script_char_setting["personality_summary"]
                
                if session_id:
                    script_state = await script_service.get_session_script_state(session_id)
                    if script_state:
                        ctx.script_state = script_state.get("state")
                        ctx.current_node_id = script_state.get("current_node_id")
                        ctx.quest_progress = script_state.get("quest_progress", 0)
                        
                        if ctx.current_node_id:
                            node = await script_service.get_node(ctx.current_node_id)
                            if node:
                                ctx.current_scene_description = node.get("description")
                                ctx.character_inner_state = node.get("character_inner_state")
                                ctx.narrative_context = node.get("narrative")
                                ctx.choices_available = node.get("choices") or []
                                ctx.emotion_gates = node.get("emotion_gate")
                                ctx.media_cue = node.get("media_cue")
                
                ctx.enabled_sections.add(PromptSection.SCRIPT_INSTRUCTION)
                ctx.enabled_sections.add(PromptSection.WORLD_SETTING)
                ctx.enabled_sections.add(PromptSection.PLOT_CONTEXT)
    
    try:
        from app.services.memory_service import MemoryService
        mem_svc = MemoryService()
        memory_ctx = await mem_svc.get_context(character_id, user_id)
        if memory_ctx:
            ctx.episodic_memories = memory_ctx.get("episodic_memories", [])
            ctx.semantic_facts = memory_ctx.get("semantic_facts", [])
    except Exception as e:
        logger.debug(f"Memory context not available: {e}")
    
    if session_id:
        ctx.session_id = session_id
        ctx.conversation_history = await chat_history_service.get_recent_messages(session_id)
    
    return ctx


@router.post("/stream")
async def chat_stream(request: Request, data: ChatStreamRequest) -> EventSourceResponse:
    llm = LLMService.get_instance()
    prompt_builder = PromptBuilder.get_instance()
    user_id = _get_user_id(request)
    user_db_id = _get_user_db_id(request)
    
    async def event_generator():
        session = await chat_history_service.get_or_create_session(
            user_id=user_id,
            character_id=data.character_id,
            session_id=data.session_id,
        )
        session_id = session["id"]
        script_id = session.get("script_id")
        
        yield SSEEvent(
            event=EventType.SESSION_CREATED,
            data={"session_id": session_id, "character_id": data.character_id}
        ).to_sse()
        
        safety_result = await content_safety.check_input(data.message)
        if not safety_result.is_safe:
            yield SSEEvent(
                event=EventType.USER_MESSAGE,
                data={"content": data.message, "role": "user"}
            ).to_sse()
            yield SSEEvent(
                event=EventType.ERROR,
                data={"message": content_safety.get_redirect_message(), "code": "CONTENT_POLICY"}
            ).to_sse()
            return
        
        if user_db_id and user_id != "guest":
            try:
                db = DatabaseService()
                user = await db.get_user_by_id(user_db_id)
                if user:
                    config = await credit_service.get_config()
                    balance = await credit_service.get_balance(user.id)
                    
                    if user.tier == "free" or not user.tier:
                        if balance["total"] < config["message_cost"]:
                            yield SSEEvent(
                                event=EventType.ERROR,
                                data={
                                    "code": "INSUFFICIENT_CREDITS",
                                    "message": f"Insufficient credits. You have {balance['total']} credits, need {config['message_cost']} for a message.",
                                    "available": balance["total"],
                                    "required": config["message_cost"],
                                }
                            ).to_sse()
                            return
                        
                        await credit_service.deduct_credits(
                            user_id=user.id,
                            amount=config["message_cost"],
                            usage_type="message",
                            character_id=data.character_id,
                            session_id=session_id,
                        )
            except Exception as e:
                logger.error(f"Credit deduction failed: {e}")
        
        yield SSEEvent(
            event=EventType.USER_MESSAGE,
            data={"content": data.message, "role": "user"}
        ).to_sse()
        
        try:
            character = await character_service.get_character_by_id(data.character_id)
            voice_id = character.get("voice_id") if character else None
            
            is_audio_intent = False
            credit_deducted = False
            remaining_credits = 0
            
            if voice_id:
                try:
                    intent_result = await llm.detect_intent(data.message)
                    is_audio_intent = intent_result.get("intent") == "audio"
                except Exception as e:
                    logger.debug(f"Intent detection failed: {e}")
                    is_audio_intent = False
            
            if is_audio_intent:
                if user_db_id and user_id != "guest":
                    try:
                        balance = await credit_service.get_balance(user_db_id)
                        if balance["total"] < VOICE_CREDIT_COST:
                            yield SSEEvent(
                                event=EventType.ERROR,
                                data={
                                    "error_code": "insufficient_credits",
                                    "required": VOICE_CREDIT_COST,
                                    "available": balance["total"],
                                    "message": "Not enough credits for voice generation"
                                }
                            ).to_sse()
                            is_audio_intent = False
                        else:
                            await credit_service.deduct_credits(
                                user_id=user_db_id,
                                amount=VOICE_CREDIT_COST,
                                usage_type="voice",
                                character_id=data.character_id,
                                session_id=session_id,
                            )
                            credit_deducted = True
                            remaining_credits = balance["total"] - VOICE_CREDIT_COST
                    except Exception as e:
                        logger.error(f"Voice credit deduction failed: {e}")
                        is_audio_intent = False
            
            decline_message = await video_intent_handler.handle_video_intent(
                user_message=data.message,
                character=character or {"name": "Assistant"},
                llm_service=llm,
            )
            
            if decline_message:
                logger.info(f"Video intent detected for character {data.character_id} - sending decline message")
                
                yield SSEEvent(
                    event=EventType.VIDEO_INTENT_DECLINED,
                    data={
                        "message": decline_message,
                        "show_photo_button": True,
                        "character_id": data.character_id,
                    }
                ).to_sse()
                
                yield SSEEvent(
                    event=EventType.STREAM_END,
                    data={"session_id": session_id}
                ).to_sse()
                return
            
            ctx = await _build_prompt_context(
                character_id=data.character_id,
                user_id=user_id,
                session_id=session_id,
                script_id=script_id,
            )
            
            messages = await prompt_builder.build_messages(
                ctx=ctx,
                user_message=data.message,
                include_history=True,
            )
            
            await chat_history_service.save_message(
                ChatMessageCreateModel(
                    session_id=session_id,
                    role="user",
                    content=data.message,
                    character_id=data.character_id,
                    user_id=user_id,
                )
            )
            
            full_response = ""
            async for chunk in llm.generate_stream(messages):
                full_response += chunk
                yield SSEEvent(
                    event=EventType.TEXT_DELTA,
                    data={"delta": chunk}
                ).to_sse()
                await asyncio.sleep(0)
            
            output_safety = await content_safety.check_output(full_response)
            if not output_safety.is_safe:
                full_response = content_safety.get_redirect_message()
            
            await chat_history_service.save_message(
                ChatMessageCreateModel(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    character_id=data.character_id,
                    user_id=user_id,
                )
            )
            
            yield SSEEvent(
                event=EventType.TEXT_DONE,
                data={"content": full_response}
            ).to_sse()
            
            if is_audio_intent and credit_deducted:
                message_id = f"msg_{uuid.uuid4().hex[:12]}"
                
                yield SSEEvent(
                    event=EventType.VOICE_NOTE_PENDING,
                    data={"message_id": message_id}
                ).to_sse()
                
                try:
                    voice_service = VoiceService()
                    audio_result = await voice_service.generate_tts(
                        text=full_response,
                        voice_id=voice_id,
                    )
                    
                    yield SSEEvent(
                        event=EventType.VOICE_NOTE_READY,
                        data={
                            "message_id": message_id,
                            "audio_url": audio_result["audio_url"],
                            "duration": audio_result["duration"],
                        }
                    ).to_sse()
                    
                    yield SSEEvent(
                        event=EventType.CREDIT_UPDATE,
                        data={"credits": remaining_credits}
                    ).to_sse()
                    
                except Exception as e:
                    logger.error(f"TTS generation failed: {e}")
                    if credit_deducted and user_db_id:
                        try:
                            await credit_service.refund_credits_simple(
                                user_id=user_db_id,
                                amount=VOICE_CREDIT_COST,
                                usage_type="voice_failed",
                                character_id=data.character_id,
                                session_id=session_id,
                            )
                            logger.info(f"Refunded {VOICE_CREDIT_COST} credits for failed TTS to user {user_db_id}")
                        except Exception as refund_error:
                            logger.error(f"Failed to refund credits for failed TTS: {refund_error}")
                    yield SSEEvent(
                        event=EventType.VOICE_NOTE_FAILED,
                        data={"message_id": message_id, "reason": str(e)}
                    ).to_sse()
            
            try:
                rel_update = await relationship_analyzer.analyze_and_update(
                    user_id=user_id,
                    character_id=data.character_id,
                    conversation=[
                        {"role": "user", "content": data.message},
                        {"role": "assistant", "content": full_response},
                    ],
                )
                
                if rel_update:
                    yield SSEEvent(
                        event=EventType.INTIMACY_UPDATED,
                        data={
                            "intimacy": rel_update.get("intimacy"),
                            "trust": rel_update.get("trust"),
                            "desire": rel_update.get("desire"),
                            "dependency": rel_update.get("dependency"),
                            "stage": rel_update.get("stage"),
                            "previous_stage": rel_update.get("previous_stage"),
                        }
                    ).to_sse()
            except Exception as e:
                logger.warning(
                    f"Relationship analysis skipped: user_id={user_id}, "
                    f"character_id={data.character_id}, error={e}"
                )
            
            yield SSEEvent(
                event=EventType.STREAM_END,
                data={"session_id": session_id}
            ).to_sse()
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield SSEEvent(
                event=EventType.ERROR,
                data={"message": str(e), "code": "STREAM_ERROR"}
            ).to_sse()
    
    return EventSourceResponse(event_generator())


@router.post("/complete-text", response_model=dict[str, Any])
async def complete_text(request: Request, data: ChatCompleteRequest) -> dict[str, Any]:
    llm = LLMService.get_instance()
    
    messages = [
        {"role": "system", "content": "Complete the following text naturally and coherently."},
    ]
    messages.extend(data.messages)
    
    try:
        response = await llm.generate(
            messages=messages,
            temperature=data.temperature,
            max_tokens=data.max_tokens
        )
        return {
            "text": response.content,
            "finish_reason": response.finish_reason,
        }
    except Exception as e:
        logger.error(f"Complete text error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message", response_model=BaseResponse)
async def send_message(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Message sent")


@router.post("/send", response_model=BaseResponse)
async def chat_send(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Chat sent")


@router.get("/sessions", response_model=dict[str, Any])
async def get_sessions(request: Request) -> dict[str, Any]:
    return {
        "sessions": [
            ChatSession(
                id="session_001",
                user_id="user_001",
                character_id="char_001",
                title="Chat with Character",
                created_at=datetime.now(),
            )
        ],
        "total": 1
    }


@router.post("/sessions", response_model=ChatSession)
async def create_session(request: Request, data: dict[str, Any]) -> ChatSession:
    return ChatSession(
        id="session_002",
        user_id="user_001",
        character_id=data.get("character_id", "char_001"),
        title="New Chat",
        created_at=datetime.now(),
    )


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(request: Request, session_id: str) -> ChatSession:
    return ChatSession(
        id=session_id,
        user_id="user_001",
        character_id="char_001",
        title="Chat Session",
        created_at=datetime.now(),
    )


@router.patch("/sessions/{session_id}/style", response_model=BaseResponse)
async def update_session_style(
    request: Request, 
    session_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    return BaseResponse(success=True, message="Style updated")


@router.patch("/sessions/{session_id}/context", response_model=BaseResponse)
async def update_session_context(
    request: Request, 
    session_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    return BaseResponse(success=True, message="Context updated")


@router.get("/sessions/{session_id}/messages", response_model=dict[str, Any])
async def get_session_messages(
    request: Request, 
    session_id: str
) -> dict[str, Any]:
    return {
        "messages": [
            ChatMessage(
                id="msg_001",
                session_id=session_id,
                role="user",
                content="Hello!",
                created_at=datetime.now(),
            ),
            ChatMessage(
                id="msg_002",
                session_id=session_id,
                role="assistant",
                content="Hi there! How can I help you?",
                created_at=datetime.now(),
            )
        ],
        "total": 2
    }


@router.post("/sessions/initialize", response_model=ChatSession)
async def initialize_session(request: Request, data: dict[str, Any]) -> ChatSession:
    return ChatSession(
        id="session_init",
        user_id="user_001",
        character_id=data.get("character_id", "char_001"),
        title="Initialized Session",
        created_at=datetime.now(),
    )


@router.post("/start_official/{official_id}", response_model=ChatSession)
async def start_official_chat(
    request: Request, 
    official_id: str
) -> ChatSession:
    return ChatSession(
        id="session_official",
        user_id="user_001",
        character_id=official_id,
        title="Official Character Chat",
        created_at=datetime.now(),
    )


@router.post("/chat_now_official/{official_id}", response_model=ChatSession)
async def chat_now_official(
    request: Request, 
    official_id: str
) -> ChatSession:
    return ChatSession(
        id="session_now",
        user_id="guest",
        character_id=official_id,
        title="Quick Chat",
        created_at=datetime.now(),
    )


@router.get("/guest/credits")
async def get_guest_credits(request: Request) -> dict[str, Any]:
    return {"credits": 5, "max_credits": 10}


@router.post("/guest/send", response_model=BaseResponse)
async def guest_send(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Guest message sent")


@router.post("/guest/audio/generate", response_model=BaseResponse)
async def guest_audio_generate(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Audio generated")


@router.post("/request-voice-note", response_model=BaseResponse)
async def request_voice_note(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Voice note requested")


@router.post("/messages/{message_id}/audio", response_model=BaseResponse)
async def add_message_audio(
    request: Request, 
    message_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    return BaseResponse(success=True, message="Audio added to message")


@router.get("/gallery/{character_id}")
async def get_character_gallery(
    request: Request, 
    character_id: str
) -> list[dict[str, Any]]:
    return [{"image_url": "https://example.com/image1.jpg", "caption": "Gallery image"}]


@router.get("/gallery")
async def get_gallery(request: Request) -> list[dict[str, Any]]:
    return [{"image_url": "https://example.com/image1.jpg", "caption": "Gallery image"}]


@router.post("/animate-image", response_model=BaseResponse)
async def animate_image(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Image animation started")


@router.post("/group/stream")
async def group_chat_stream(
    request: Request,
    data: dict[str, Any],
) -> EventSourceResponse:
    from app.models import GroupChatStreamRequest
    from app.services.group_chat_service import group_chat_service
    
    validated_data = GroupChatStreamRequest(**data)
    user_id = _get_user_id(request)
    user_db_id = _get_user_db_id(request)
    
    async def event_generator():
        session = await group_chat_service.get_or_create_session(
            user_id=user_id,
            participants=validated_data.participants,
            session_id=validated_data.session_id,
        )
        session_id = session["id"]
        
        yield SSEEvent(
            event=EventType.SESSION_CREATED,
            data={
                "session_id": session_id,
                "participants": validated_data.participants,
                "is_group": True
            }
        ).to_sse()
        
        safety_result = await content_safety.check_input(validated_data.message)
        if not safety_result.is_safe:
            yield SSEEvent(
                event=EventType.USER_MESSAGE,
                data={"content": validated_data.message, "role": "user"}
            ).to_sse()
            yield SSEEvent(
                event=EventType.ERROR,
                data={"message": content_safety.get_redirect_message(), "code": "CONTENT_POLICY"}
            ).to_sse()
            return
        
        if user_db_id and user_id != "guest":
            try:
                db_svc = DatabaseService()
                user = await db_svc.get_user_by_id(user_db_id)
                if user:
                    config = await credit_service.get_config()
                    balance = await credit_service.get_balance(user.id)
                    
                    group_cost = config["message_cost"] * len(validated_data.participants)
                    
                    if user.tier == "free" or not user.tier:
                        if balance["total"] < group_cost:
                            yield SSEEvent(
                                event=EventType.ERROR,
                                data={
                                    "code": "INSUFFICIENT_CREDITS",
                                    "message": f"Insufficient credits for group chat. You have {balance['total']}, need {group_cost}.",
                                    "available": balance["total"],
                                    "required": group_cost,
                                }
                            ).to_sse()
                            return
                        
                        await credit_service.deduct_credits(
                            user_id=user.id,
                            amount=group_cost,
                            usage_type="group_message",
                            character_id=validated_data.participants[0],
                            session_id=session_id,
                            description=f"Group chat with {len(validated_data.participants)} characters",
                        )
                        
                        yield SSEEvent(
                            event=EventType.CREDIT_UPDATE,
                            data={"credits": balance["total"] - group_cost}
                        ).to_sse()
            except Exception as e:
                logger.error(f"Group chat credit deduction failed: {e}")
        
        yield SSEEvent(
            event=EventType.USER_MESSAGE,
            data={"content": validated_data.message, "role": "user"}
        ).to_sse()
        
        await group_chat_service.save_group_message(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=validated_data.message,
        )
        
        conversation_history = await group_chat_service.get_group_messages(session_id)
        
        try:
            async for event in group_chat_service.stream_parallel_responses(
                participants=validated_data.participants,
                user_id=user_id,
                message=validated_data.message,
                conversation_history=conversation_history,
            ):
                event_type = event.get("event")
                event_data = event.get("data", {})
                
                if event_type == "text_delta":
                    yield SSEEvent(
                        event=EventType.TEXT_DELTA,
                        data=event_data
                    ).to_sse()
                
                elif event_type == "text_done":
                    await group_chat_service.save_group_message(
                        session_id=session_id,
                        user_id=user_id,
                        role="assistant",
                        content=event_data.get("full_content", ""),
                        speaker_id=event_data.get("speaker_id"),
                    )
                    yield SSEEvent(
                        event=EventType.TEXT_DONE,
                        data=event_data
                    ).to_sse()
                
                elif event_type == "error":
                    yield SSEEvent(
                        event=EventType.ERROR,
                        data=event_data
                    ).to_sse()
            
        except Exception as e:
            logger.error(f"Group chat stream error: {e}")
            yield SSEEvent(
                event=EventType.ERROR,
                data={"message": str(e), "code": "GROUP_STREAM_ERROR"}
            ).to_sse()
        
        yield SSEEvent(
            event=EventType.STREAM_END,
            data={"session_id": session_id}
        ).to_sse()
    
    return EventSourceResponse(event_generator())


@router.post("/group/sessions")
async def create_group_session(
    request: Request,
    data: dict[str, Any],
) -> dict[str, Any]:
    from app.services.group_chat_service import group_chat_service
    
    user_id = _get_user_id(request)
    participants = data.get("participants", [])
    
    if not participants or len(participants) < 2:
        raise HTTPException(status_code=400, detail="At least 2 participants required")
    
    session = await group_chat_service.create_group_session(
        user_id=user_id,
        participants=participants,
        title=data.get("title"),
    )
    
    return session


@router.get("/group/sessions/{session_id}")
async def get_group_session(
    request: Request,
    session_id: str,
) -> dict[str, Any]:
    from app.services.group_chat_service import group_chat_service
    
    session = await group_chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session


@router.get("/group/sessions/{session_id}/messages")
async def get_group_session_messages(
    request: Request,
    session_id: str,
    limit: int = 50,
) -> dict[str, Any]:
    from app.services.group_chat_service import group_chat_service
    
    session = await group_chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await group_chat_service.get_group_messages(session_id, limit)
    
    return {"session_id": session_id, "messages": messages}