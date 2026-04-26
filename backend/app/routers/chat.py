import json
import logging
import asyncio
import uuid
import random
import re
import hashlib
import time
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Response, status
from typing import Any, Optional
from sse_starlette.sse import EventSourceResponse

from app.models import (
    BaseResponse, ChatStreamRequest, ChatCompleteRequest,
    ChatSession, ChatMessage, ChatMessageCreate as ChatMessageCreateModel,
    ChatSessionUpdate, ChatSessionCreate as ChatSessionCreateModel,
)
from app.core.events import EventType, SSEEvent
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
from app.services.auth_service import jwt_service
from app.core.dependencies import get_firebase_service
from app.services.script_library_service import script_library_service
from app.core.database import db

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)

STORY_COMPLETION_MARKER = re.compile(r"\[\[STORY_COMPLETED:(good|neutral|bad|secret)\]\]", re.IGNORECASE)

GUEST_MAX_CREDITS = 20.0
GUEST_STATE_TTL_SECONDS = 24 * 60 * 60
_guest_states: dict[str, dict[str, Any]] = {}


def _extract_access_token(request: Request) -> Optional[str]:
    auth_header = (request.headers.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
        if token:
            return token
    cookie_token = (request.cookies.get("access_token") or "").strip()
    return cookie_token or None


def _resolve_authenticated_user_id(request: Request) -> Optional[str]:
    token = _extract_access_token(request)
    if not token:
        return None

    payload = jwt_service.verify_token(token)
    if payload and payload.get("sub"):
        return str(payload["sub"])

    try:
        firebase_service = get_firebase_service()
        if getattr(firebase_service, "_initialized", False):
            decoded = firebase_service.verify_token(token)
            if decoded and decoded.get("uid"):
                return str(decoded["uid"])
    except Exception:
        pass
    return None


def _replace_script_placeholders(data: Any, character_name: str) -> Any:
    if isinstance(data, str):
        return data.replace("{{character_name}}", character_name)
    if isinstance(data, dict):
        return {k: _replace_script_placeholders(v, character_name) for k, v in data.items()}
    if isinstance(data, list):
        return [_replace_script_placeholders(item, character_name) for item in data]
    return data


def _get_user_id(request: Request) -> str:
    state_user_id = getattr(request.state, "user_id", None)
    if state_user_id:
        return str(state_user_id)
    resolved_user_id = _resolve_authenticated_user_id(request)
    return resolved_user_id or "guest"


def _get_user_db_id(request: Request) -> Optional[str]:
    state_user_db_id = getattr(request.state, "user_db_id", None)
    if state_user_db_id:
        return str(state_user_db_id)
    resolved_user_id = _resolve_authenticated_user_id(request)
    return str(resolved_user_id) if resolved_user_id else None


def _resolve_guest_id(request: Request, response: Optional[Response] = None) -> str:
    cookie_id = request.cookies.get("guest_id")
    if cookie_id:
        if response is not None:
            response.set_cookie(
                key="guest_id",
                value=cookie_id,
                max_age=GUEST_STATE_TTL_SECONDS,
                httponly=True,
                samesite="lax",
            )
        return cookie_id

    header_fingerprint = request.headers.get("x-device-fingerprint")
    if header_fingerprint:
        guest_id = f"fp_{header_fingerprint[:64]}"
    else:
        ip = (request.client.host if request.client else "0.0.0.0").strip()
        ua = (request.headers.get("user-agent") or "unknown").strip()
        digest = hashlib.sha256(f"{ip}|{ua}".encode("utf-8")).hexdigest()
        guest_id = f"anon_{digest[:32]}"

    if response is not None:
        response.set_cookie(
            key="guest_id",
            value=guest_id,
            max_age=GUEST_STATE_TTL_SECONDS,
            httponly=True,
            samesite="lax",
        )
    return guest_id


def _get_guest_state(guest_id: str) -> dict[str, Any]:
    now = int(time.time())
    state = _guest_states.get(guest_id)
    if not state or now - int(state.get("updated_at", 0)) > GUEST_STATE_TTL_SECONDS:
        state = {
            "credits_remaining": GUEST_MAX_CREDITS,
            "updated_at": now,
        }
        _guest_states[guest_id] = state
    else:
        state["updated_at"] = now
    return state


async def _get_usage_cost(usage_type: str) -> float:
    config = await credit_service.get_config()
    amount_map = {
        "message": float(config.get("message_cost", 0)),
        "voice": float(config.get("voice_cost", 0)),
        "image": float(config.get("image_cost", 0)),
        "video": float(config.get("video_cost", 0)),
    }
    return float(amount_map.get(usage_type, 0))


def _render_guest_fallback(character_name: str, user_message: str) -> str:
    message = (user_message or "").strip()
    if not message:
        return f"I'm here with you. What would you like to talk about?"
    return (
        f"{character_name}: I heard you say \"{message}\". "
        "Tell me more and we can keep going."
    )


def _compose_script_opening(
    *,
    character_name: str,
    personality: str,
    opening_line: str,
    opening_scene: str,
    world_setting: str,
    user_role: str,
) -> str:
    base = opening_line.strip()
    if not base:
        if opening_scene:
            base = f"*{opening_scene}*"
        elif world_setting:
            base = f"We're in {world_setting}."
        elif personality:
            base = f"Hi, I'm {character_name}. {personality}"
        else:
            base = f"Hi, I'm {character_name}."

    if user_role:
        starter = (
            f"You are {user_role} in this story. "
            "Start by telling me your first move in this scene."
        )
    elif opening_scene or world_setting:
        starter = "Start by telling me what you do first in this scene."
    else:
        starter = "Start by telling me what kind of moment you want to have."

    return f"{base}\n\n{starter}"


async def _build_script_opening(
    character: Optional[dict[str, Any]],
    character_id: str,
    script_id: Optional[str],
) -> Optional[str]:
    sid = str(script_id or "").strip()
    if not sid:
        return None

    name = (
        (character or {}).get("first_name")
        or (character or {}).get("name")
        or character_id
        or "AI"
    )
    personality = ((character or {}).get("personality_summary") or "").strip()

    if sid.startswith("ethical_") or sid.startswith("script_lib_"):
        script_lib = await script_library_service.get_script(sid)
        if not script_lib:
            return None

        full_script = script_lib.full_script if isinstance(script_lib.full_script, dict) else {}
        opening_line = str(
            full_script.get("opening_line")
            or full_script.get("opening")
            or full_script.get("opening_message")
            or ""
        ).strip()
        opening_scene = str(full_script.get("opening_scene") or full_script.get("prologue") or "").strip()
        world_setting = str(getattr(script_lib, "summary", "") or "").strip()

        return _compose_script_opening(
            character_name=name,
            personality=personality,
            opening_line=opening_line,
            opening_scene=opening_scene,
            world_setting=world_setting,
            user_role="",
        )

    script = await script_service.get_script(sid)
    if not script:
        return None

    return _compose_script_opening(
        character_name=name,
        personality=personality,
        opening_line=str(script.get("opening_line") or "").strip(),
        opening_scene=str(script.get("opening_scene") or "").strip(),
        world_setting=str(script.get("world_setting") or "").strip(),
        user_role=str(script.get("user_role") or "").strip(),
    )


async def _build_character_opening(
    character: Optional[dict[str, Any]],
    character_id: str,
    script_id: Optional[str] = None,
) -> str:
    script_opening = await _build_script_opening(character, character_id, script_id)
    if script_opening:
        return script_opening

    if character and isinstance(character.get("greeting"), str):
        greeting = character["greeting"].strip()
        if greeting:
            return f"{greeting}\n\nStart by telling me what's on your mind right now."

    name = (
        (character or {}).get("first_name")
        or (character or {}).get("name")
        or character_id
        or "AI"
    )
    personality = ((character or {}).get("personality_summary") or "").strip()
    if personality:
        return (
            f"Hi, I'm {name}. {personality}\n\n"
            "Start by telling me what kind of vibe you want right now."
        )
    return (
        f"Hi, I'm {name}. It's great to meet you.\n\n"
        f"If you want an easy start, say: \"Hey {name}, how should we begin?\""
    )


def _parse_json_dict(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return {}


def _extract_story_completion_marker(text: str) -> tuple[str, Optional[str]]:
    match = STORY_COMPLETION_MARKER.search(text or "")
    if not match:
        return text, None
    ending_type = match.group(1).lower()
    cleaned = STORY_COMPLETION_MARKER.sub("", text).strip()
    return cleaned, ending_type


async def _list_bound_scripts(character_id: str) -> list[dict[str, Any]]:
    try:
        rows = await db.execute(
            """
            SELECT b.script_id, b.weight, s.title
            FROM character_script_bindings b
            JOIN script_library s ON s.id = b.script_id
            WHERE b.character_id = ?
              AND b.is_active = 1
              AND s.status = 'published'
            """,
            (character_id,),
            fetch_all=True,
        )
    except Exception as e:
        logger.debug(f"Failed to read character script bindings: {e}")
        return []
    scripts: list[dict[str, Any]] = []
    for row in rows or []:
        try:
            weight = int(row.get("weight") or 1)
        except (TypeError, ValueError):
            weight = 1
        scripts.append({
            "id": row.get("script_id"),
            "title": row.get("title") or row.get("script_id"),
            "weight": max(1, weight),
        })
    return [s for s in scripts if s.get("id")]


def _pick_weighted_script(candidates: list[dict[str, Any]], excluded_ids: set[str]) -> Optional[dict[str, Any]]:
    if not candidates:
        return None
    pool = [c for c in candidates if c.get("id") not in excluded_ids]
    if not pool:
        pool = candidates
    total = sum(max(1, int(c.get("weight", 1))) for c in pool)
    pivot = random.uniform(0, total)
    running = 0.0
    for item in pool:
        running += max(1, int(item.get("weight", 1)))
        if pivot <= running:
            return item
    return pool[-1]


async def _assign_or_rotate_bound_script(
    session_id: str,
    character_id: str,
    *,
    force_rotate: bool = False,
    completed_script_id: Optional[str] = None,
) -> tuple[Optional[str], Optional[str], bool]:
    session = await chat_history_service.get_session(session_id)
    if not session:
        return None, None, False

    bindings = await _list_bound_scripts(character_id)
    if not bindings:
        return session.get("script_id"), None, False

    context = _parse_json_dict(session.get("context"))
    rotation = _parse_json_dict(context.get("script_rotation"))
    completed_ids = [str(x) for x in rotation.get("completed_ids", []) if x]
    current_script_id = session.get("script_id")

    if completed_script_id:
        if completed_script_id in completed_ids:
            completed_ids.remove(completed_script_id)
        completed_ids.append(completed_script_id)
        completed_ids = completed_ids[-50:]

    if not force_rotate and current_script_id:
        current = next((item for item in bindings if item["id"] == current_script_id), None)
        if current:
            return current_script_id, current.get("title"), False

    selected = _pick_weighted_script(bindings, set(completed_ids) if force_rotate else set())
    if not selected:
        return current_script_id, None, False

    next_script_id = selected["id"]
    next_script_title = selected.get("title")
    changed = next_script_id != current_script_id

    rotation["completed_ids"] = completed_ids
    rotation["current_id"] = next_script_id
    rotation["updated_at"] = datetime.utcnow().isoformat()
    context["script_rotation"] = rotation

    if changed or force_rotate:
        await chat_history_service.update_session(
            session_id,
            ChatSessionUpdate(script_id=next_script_id, context=context),
        )

    return next_script_id, next_script_title, changed


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

        if ctx.use_script_library and ctx.script_library_full:
            beats = ctx.script_library_full.get("narrative_beats") or []
            if beats:
                previous_user_turns = sum(
                    1 for msg in ctx.conversation_history
                    if msg.get("role") == "user"
                )
                current_turn = previous_user_turns + 1
                beat_index = min(len(beats) - 1, max(0, (current_turn - 1) // 3))
                current_beat = beats[beat_index] if isinstance(beats[beat_index], dict) else {}
                next_beat = (
                    beats[beat_index + 1]
                    if beat_index + 1 < len(beats) and isinstance(beats[beat_index + 1], dict)
                    else None
                )

                if current_beat.get("scene"):
                    ctx.current_scene_description = current_beat["scene"]

                guidance_parts = []
                if current_beat.get("hint"):
                    guidance_parts.append(f"Current beat guidance: {current_beat['hint']}")
                if current_beat.get("emotion"):
                    guidance_parts.append(f"Emotional tone: {current_beat['emotion']}")
                if next_beat:
                    next_scene = next_beat.get("scene")
                    next_hint = next_beat.get("hint")
                    if next_scene:
                        guidance_parts.append(f"Steer naturally toward next beat: {next_scene}")
                    if next_hint:
                        guidance_parts.append(f"Next beat hint: {next_hint}")
                if guidance_parts:
                    ctx.narrative_context = "\n".join(guidance_parts)
    
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

        assigned_script_id, assigned_script_title, assigned_changed = await _assign_or_rotate_bound_script(
            session_id,
            data.character_id,
        )
        if assigned_script_id:
            script_id = assigned_script_id
            if assigned_changed:
                yield SSEEvent(
                    event=EventType.SCRIPT_STATE_UPDATED,
                    data={
                        "session_id": session_id,
                        "script_id": assigned_script_id,
                        "script_title": assigned_script_title or assigned_script_id,
                        "reason": "random_assigned",
                    },
                ).to_sse()
        
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
        
        message_cost = await _get_usage_cost("message")
        if user_db_id and user_id != "guest":
            try:
                db = DatabaseService()
                user = await db.get_user_by_id(user_db_id)
                if user:
                    balance = await credit_service.get_balance(user.id)
                    
                    if user.tier == "free" or not user.tier:
                        if balance["total"] < message_cost:
                            yield SSEEvent(
                                event=EventType.ERROR,
                                data={
                                    "code": "INSUFFICIENT_CREDITS",
                                    "message": f"Insufficient credits. You have {balance['total']} credits, need {message_cost} for a message.",
                                    "available": balance["total"],
                                    "required": message_cost,
                                }
                            ).to_sse()
                            return
                        
                        await credit_service.deduct_credits(
                            user_id=user.id,
                            amount=message_cost,
                            usage_type="message",
                            character_id=data.character_id,
                            session_id=session_id,
                        )
            except Exception as e:
                logger.error(f"Credit deduction failed: {e}")
        elif user_id == "guest":
            guest_state = _get_guest_state(_resolve_guest_id(request))
            guest_remaining = float(guest_state.get("credits_remaining", GUEST_MAX_CREDITS))
            if guest_remaining < message_cost:
                yield SSEEvent(
                    event=EventType.ERROR,
                    data={
                        "error_code": "guest_credits_exhausted",
                        "message": "Guest credits exhausted. Please register to continue chatting.",
                        "available": guest_remaining,
                        "required": message_cost,
                    },
                ).to_sse()
                return
            guest_state["credits_remaining"] = max(0.0, guest_remaining - message_cost)
            guest_state["updated_at"] = int(time.time())
        
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
            voice_cost = await _get_usage_cost("voice")
            
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
                        if balance["total"] < voice_cost:
                            yield SSEEvent(
                                event=EventType.ERROR,
                                data={
                                    "error_code": "insufficient_credits",
                                    "required": voice_cost,
                                    "available": balance["total"],
                                    "message": "Not enough credits for voice generation"
                                }
                            ).to_sse()
                            is_audio_intent = False
                        else:
                            await credit_service.deduct_credits(
                                user_id=user_db_id,
                                amount=voice_cost,
                                usage_type="voice",
                                character_id=data.character_id,
                                session_id=session_id,
                            )
                            credit_deducted = True
                            remaining_credits = balance["total"] - voice_cost
                    except Exception as e:
                        logger.error(f"Voice credit deduction failed: {e}")
                        is_audio_intent = False
                elif user_id == "guest":
                    guest_state = _get_guest_state(_resolve_guest_id(request))
                    guest_remaining = float(guest_state.get("credits_remaining", GUEST_MAX_CREDITS))
                    if guest_remaining < voice_cost:
                        is_audio_intent = False
                    else:
                        guest_state["credits_remaining"] = max(0.0, guest_remaining - voice_cost)
                        guest_state["updated_at"] = int(time.time())
            
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
            full_response, ending_type = _extract_story_completion_marker(full_response)
            
            saved_assistant_message = await chat_history_service.save_message(
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
                data={
                    "message_id": saved_assistant_message["id"],
                    "full_content": full_response,
                    "content": full_response,
                }
            ).to_sse()

            if ending_type and script_id:
                completed_script_id = script_id
                completed_script = await script_library_service.get_script(script_id)
                completed_title = completed_script.title if completed_script else script_id

                next_script_id, next_script_title, switched = await _assign_or_rotate_bound_script(
                    session_id,
                    data.character_id,
                    force_rotate=True,
                    completed_script_id=script_id,
                )
                if next_script_id:
                    script_id = next_script_id

                yield SSEEvent(
                    event=EventType.STORY_COMPLETED,
                    data={
                        "story_id": completed_script.id if completed_script else completed_script_id,
                        "story_title": completed_title,
                        "ending_type": ending_type,
                        "rewards": {},
                        "completion_time_minutes": None,
                        "narrative": "",
                        "next_script_id": next_script_id,
                        "next_script_title": next_script_title,
                    }
                ).to_sse()

                if switched and next_script_id:
                    yield SSEEvent(
                        event=EventType.SCRIPT_STATE_UPDATED,
                        data={
                            "session_id": session_id,
                            "script_id": next_script_id,
                            "script_title": next_script_title or next_script_id,
                            "reason": "rotated_after_completion",
                        },
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
                                amount=voice_cost,
                                usage_type="voice_failed",
                                character_id=data.character_id,
                                session_id=session_id,
                            )
                            logger.info(f"Refunded {voice_cost} credits for failed TTS to user {user_db_id}")
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
async def get_sessions(
    request: Request,
    character_id: Optional[str] = None,
    limit: int = 20,
) -> dict[str, Any]:
    user_id = _get_user_id(request)
    safe_limit = max(1, min(limit, 100))
    sessions = await chat_history_service.get_user_sessions(
        user_id=user_id,
        character_id=character_id,
        limit=safe_limit,
    )
    return {
        "sessions": sessions,
        "total": len(sessions),
    }


@router.post("/sessions", response_model=ChatSession)
async def create_session(request: Request, data: dict[str, Any]) -> ChatSession:
    character_id = str(data.get("character_id") or "").strip()
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id is required")

    session = await chat_history_service.create_session(
        ChatSessionCreateModel(
            user_id=_get_user_id(request),
            character_id=character_id,
            script_id=data.get("script_id"),
            context=data.get("context") if isinstance(data.get("context"), dict) else None,
        )
    )

    if data.get("title") is not None:
        updated = await chat_history_service.update_session(
            session["id"],
            ChatSessionUpdate(title=str(data.get("title"))),
        )
        if updated:
            session = updated

    if session.get("context") is None:
        session["context"] = {}

    return session


@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_session(request: Request, session_id: str) -> ChatSession:
    session = await chat_history_service.get_session(session_id)
    if not session:
        now = datetime.utcnow()
        return ChatSession(
            id=session_id,
            user_id=_get_user_id(request),
            character_id="unknown",
            title="Chat Session",
            context={},
            created_at=now,
            updated_at=now,
        )
    return session


@router.patch("/sessions/{session_id}/style", response_model=BaseResponse)
async def update_session_style(
    request: Request, 
    session_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    session = await chat_history_service.get_session(session_id)
    if not session:
        return BaseResponse(success=True, message="Style updated")

    style = data.get("style")
    if style is None:
        raise HTTPException(status_code=400, detail="style is required")

    context = session.get("context") if isinstance(session.get("context"), dict) else {}
    context["style"] = str(style)
    await chat_history_service.update_session(
        session_id,
        ChatSessionUpdate(context=context),
    )
    return BaseResponse(success=True, message="Style updated")


@router.patch("/sessions/{session_id}/context", response_model=BaseResponse)
async def update_session_context(
    request: Request, 
    session_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    session = await chat_history_service.get_session(session_id)
    if not session:
        return BaseResponse(success=True, message="Context updated")
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="context body must be object")

    context = session.get("context") if isinstance(session.get("context"), dict) else {}
    context.update(data)
    await chat_history_service.update_session(
        session_id,
        ChatSessionUpdate(context=context),
    )
    return BaseResponse(success=True, message="Context updated")


@router.get("/sessions/{session_id}/messages", response_model=dict[str, Any])
async def get_session_messages(
    request: Request, 
    session_id: str,
    limit: int = 20,
    before_id: Optional[str] = None,
) -> dict[str, Any]:
    session = await chat_history_service.get_session(session_id)
    if not session:
        return {
            "messages": [],
            "has_more": False,
            "oldest_message_id": None,
            "total_count": 0,
        }

    safe_limit = max(1, min(limit, 100))
    if before_id:
        messages = await chat_history_service.get_messages_before(
            session_id=session_id,
            before_message_id=before_id,
            limit=safe_limit,
        )
        messages = list(reversed(messages))
    else:
        rows = await db.execute(
            """SELECT * FROM chat_messages
               WHERE session_id = ?
               ORDER BY created_at DESC
               LIMIT ?""",
            (session_id, safe_limit),
            fetch_all=True,
        )
        messages = [
            chat_history_service._message_row_to_dict(row)  # noqa: SLF001
            for row in reversed(rows or [])
        ]

    total_row = await db.execute(
        "SELECT COUNT(*) as count FROM chat_messages WHERE session_id = ?",
        (session_id,),
        fetch=True,
    )
    total_count = int(total_row["count"]) if total_row else len(messages)
    oldest_message_id = messages[0]["id"] if messages else None
    has_more = total_count > len(messages)
    if before_id and messages:
        first_created_at = messages[0].get("created_at")
        older_count_row = await db.execute(
            "SELECT COUNT(*) as count FROM chat_messages WHERE session_id = ? AND created_at < ?",
            (session_id, first_created_at),
            fetch=True,
        )
        has_more = bool(older_count_row and int(older_count_row["count"]) > 0)

    normalized_messages: list[dict[str, Any]] = []
    for m in messages:
        image_urls = m.get("image_urls") or []
        first_image_url = image_urls[0] if isinstance(image_urls, list) and image_urls else None
        metadata = m.get("metadata") if isinstance(m.get("metadata"), dict) else {}
        video_url = metadata.get("video_url") if isinstance(metadata.get("video_url"), str) else None
        normalized_messages.append(
            {
                **m,
                "timestamp": m.get("created_at"),
                "image_url": first_image_url,
                "video_url": video_url,
            }
        )

    return {
        "messages": normalized_messages,
        "has_more": has_more,
        "oldest_message_id": oldest_message_id,
        "total_count": total_count,
    }


@router.post("/sessions/initialize", response_model=dict[str, Any])
async def initialize_session(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    character_id = str(data.get("character_id") or "").strip()
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id is required")

    session, opening_message, opening_message_id, is_new = await _initialize_character_session(
        user_id=_get_user_id(request),
        character_id=character_id,
    )

    return {
        **session,
        "session_id": session["id"],
        "is_new": is_new,
        "scene": None,
        "synopsis": None,
        "opening_message": opening_message,
        "message_id": opening_message_id,
    }


async def _initialize_character_session(
    user_id: str,
    character_id: str,
) -> tuple[dict[str, Any], Optional[str], Optional[str], bool]:
    existing = await chat_history_service.get_user_sessions(
        user_id=user_id,
        character_id=character_id,
        limit=1,
    )
    is_new = False
    if existing:
        session = existing[0]
    else:
        session = await chat_history_service.create_session(
            ChatSessionCreateModel(
                user_id=user_id,
                character_id=character_id,
            )
        )
        is_new = True

    if not isinstance(session.get("context"), dict):
        session["context"] = {}

    opening_message: Optional[str] = None
    opening_message_id: Optional[str] = None

    existing_messages = await chat_history_service.get_recent_messages(session["id"], limit=1)
    if existing_messages:
        msg = existing_messages[-1]
        if msg.get("role") == "assistant" and isinstance(msg.get("content"), str):
            opening_message = msg["content"]
            opening_message_id = msg.get("id")
    else:
        assigned_script_id, _, _ = await _assign_or_rotate_bound_script(
            session["id"],
            character_id,
        )
        if assigned_script_id:
            session["script_id"] = assigned_script_id

        character = await character_service.get_character_by_id(character_id)
        opening_message = await _build_character_opening(
            character,
            character_id,
            script_id=session.get("script_id"),
        )
        saved_opening = await chat_history_service.save_message(
            ChatMessageCreateModel(
                session_id=session["id"],
                role="assistant",
                content=opening_message,
                character_id=character_id,
                user_id=user_id,
            )
        )
        opening_message_id = saved_opening.get("id")

    return session, opening_message, opening_message_id, is_new


@router.post("/start_official/{official_id}", response_model=ChatSession)
async def start_official_chat(
    request: Request, 
    official_id: str
) -> ChatSession:
    session, _, _, _ = await _initialize_character_session(
        user_id=_get_user_id(request),
        character_id=official_id,
    )
    return ChatSession(**session)


@router.post("/chat_now_official/{official_id}", response_model=ChatSession)
async def chat_now_official(
    request: Request, 
    official_id: str
) -> ChatSession:
    user_id = _get_user_id(request)
    character = await character_service.get_or_create_official_clone(official_id, user_id)
    if not character:
        raise HTTPException(status_code=404, detail="Official character not found")

    session, _, _, _ = await _initialize_character_session(
        user_id=user_id,
        character_id=character["id"],
    )
    return ChatSession(**session)


@router.get("/guest/credits")
async def get_guest_credits(request: Request, response: Response) -> dict[str, Any]:
    guest_id = _resolve_guest_id(request, response)
    state = _get_guest_state(guest_id)
    credits_remaining = max(0.0, float(state.get("credits_remaining", GUEST_MAX_CREDITS)))
    return {
        "credits": credits_remaining,
        "max_credits": GUEST_MAX_CREDITS,
        "is_exhausted": credits_remaining <= 0,
    }


@router.post("/guest/send")
async def guest_send(request: Request, response: Response, data: dict[str, Any]) -> dict[str, Any]:
    character_id = str(data.get("character_id") or "").strip()
    message = str(data.get("message") or "").strip()

    if not character_id:
        raise HTTPException(status_code=400, detail="character_id is required")
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    character = await character_service.get_character_by_id(character_id) or {
        "name": "AI",
        "personality_summary": "",
        "backstory": "",
    }

    guest_id = _resolve_guest_id(request, response)
    state = _get_guest_state(guest_id)
    message_cost = await _get_usage_cost("message")
    credits_remaining = max(0.0, float(state.get("credits_remaining", GUEST_MAX_CREDITS)))
    if credits_remaining < message_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error_code": "guest_credits_exhausted",
                "message": "Guest credits exhausted. Please register to continue chatting.",
                "credits_remaining": 0,
                "is_exhausted": True,
            },
        )

    llm = LLMService.get_instance()
    character_name = character.get("first_name") or character.get("name") or "AI"
    personality_summary = character.get("personality_summary") or ""
    backstory = character.get("backstory") or ""

    system_prompt = (
        "You are roleplaying as the following AI companion.\n"
        f"Name: {character_name}\n"
        f"Personality: {personality_summary}\n"
        f"Backstory: {backstory}\n"
        "Reply naturally, warmly, and keep it concise (1-3 short paragraphs)."
    )

    try:
        llm_response = await llm.generate(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.8,
            max_tokens=220,
        )
        assistant_content = (llm_response.content or "").strip()
        if not assistant_content:
            assistant_content = _render_guest_fallback(character_name, message)
    except Exception as e:
        logger.warning(f"Guest chat LLM failed, using fallback response: {e}")
        assistant_content = _render_guest_fallback(character_name, message)

    next_credits = max(0.0, credits_remaining - message_cost)
    state["credits_remaining"] = next_credits
    state["updated_at"] = int(time.time())

    return {
        "success": True,
        "content": assistant_content,
        "credits_remaining": next_credits,
        "is_exhausted": next_credits <= 0,
    }


@router.post("/guest/audio/generate")
async def guest_audio_generate(request: Request, response: Response, data: dict[str, Any]) -> dict[str, Any]:
    text = str(data.get("text") or "").strip()
    character_id = str(data.get("character_id") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    if not character_id:
        raise HTTPException(status_code=400, detail="character_id is required")

    guest_id = _resolve_guest_id(request, response)
    state = _get_guest_state(guest_id)
    voice_cost = await _get_usage_cost("voice")
    credits_remaining = max(0.0, float(state.get("credits_remaining", GUEST_MAX_CREDITS)))
    if credits_remaining < voice_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error_code": "guest_credits_exhausted",
                "message": "Guest credits exhausted. Please register to continue.",
                "credits_remaining": credits_remaining,
                "required": voice_cost,
                "is_exhausted": True,
            },
        )

    character = await character_service.get_character_by_id(character_id)
    voice_id = (character or {}).get("voice_id")
    if not voice_id:
        raise HTTPException(status_code=400, detail="Character voice is not configured")

    state["credits_remaining"] = max(0.0, credits_remaining - voice_cost)
    state["updated_at"] = int(time.time())

    try:
        voice_service = VoiceService()
        audio_result = await voice_service.generate_tts(text=text, voice_id=voice_id)
        return {
            "success": True,
            "audio_url": audio_result.get("audio_url"),
            "duration": audio_result.get("duration"),
            "credits_remaining": state["credits_remaining"],
            "is_exhausted": state["credits_remaining"] <= 0,
        }
    except Exception:
        state["credits_remaining"] = credits_remaining
        state["updated_at"] = int(time.time())
        raise


@router.post("/request-voice-note", response_model=BaseResponse)
async def request_voice_note(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Voice note requested")


@router.post("/messages/{message_id}/audio", response_model=dict[str, Any])
async def add_message_audio(
    request: Request, 
    message_id: str, 
    data: Optional[dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> dict[str, Any]:
    payload = data or {}
    effective_session_id = str(payload.get("session_id") or session_id or "").strip()
    message = await chat_history_service.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if effective_session_id and message.get("session_id") != effective_session_id:
        raise HTTPException(status_code=404, detail="Message not found in session")

    cached_audio_url = str(message.get("audio_url") or "").strip()
    if cached_audio_url:
        return {
            "success": True,
            "message": "Audio already available",
            "audio_url": cached_audio_url,
            "cached": True,
            "credits_deducted": False,
        }

    text = str(message.get("content") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message has no text to synthesize")

    character_id = str(message.get("character_id") or "").strip()
    character = await character_service.get_character_by_id(character_id) if character_id else None
    voice_id = (character or {}).get("voice_id")
    if not voice_id:
        raise HTTPException(status_code=400, detail="Character voice is not configured")

    user_id = _get_user_id(request)
    user_db_id = _get_user_db_id(request)
    voice_cost = await _get_usage_cost("voice")
    credits_deducted = False
    remaining_credits: Optional[float] = None
    guest_state: Optional[dict[str, Any]] = None
    guest_original_credits: Optional[float] = None

    if user_db_id and user_id != "guest":
        balance = await credit_service.get_balance(user_db_id)
        if balance["total"] < voice_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error_code": "insufficient_credits",
                    "required": voice_cost,
                    "available": balance["total"],
                    "message": "Not enough credits for voice generation",
                },
            )
        await credit_service.deduct_credits(
            user_id=user_db_id,
            amount=voice_cost,
            usage_type="voice",
            character_id=character_id,
            session_id=message.get("session_id"),
        )
        credits_deducted = True
        remaining_credits = balance["total"] - voice_cost
    elif user_id == "guest":
        guest_state = _get_guest_state(_resolve_guest_id(request))
        guest_remaining = float(guest_state.get("credits_remaining", GUEST_MAX_CREDITS))
        guest_original_credits = guest_remaining
        if guest_remaining < voice_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error_code": "guest_credits_exhausted",
                    "required": voice_cost,
                    "available": guest_remaining,
                    "message": "Guest credits exhausted. Please register to continue.",
                },
            )
        guest_state["credits_remaining"] = max(0.0, guest_remaining - voice_cost)
        guest_state["updated_at"] = int(time.time())
        credits_deducted = voice_cost > 0
        remaining_credits = guest_state["credits_remaining"]

    try:
        voice_service = VoiceService()
        audio_result = await voice_service.generate_tts(
            text=text,
            voice_id=voice_id,
        )
        audio_url = audio_result.get("audio_url")
        if not audio_url:
            raise HTTPException(status_code=500, detail="Voice provider did not return audio")

        await db.execute(
            "UPDATE chat_messages SET audio_url = ? WHERE id = ?",
            (audio_url, message_id),
        )

        return {
            "success": True,
            "message": "Audio generated",
            "audio_url": audio_url,
            "duration": audio_result.get("duration"),
            "cached": False,
            "credits_deducted": credits_deducted,
            "credits_remaining": remaining_credits,
        }
    except Exception:
        if credits_deducted and user_db_id and user_id != "guest":
            try:
                await credit_service.refund_credits_simple(
                    user_id=user_db_id,
                    amount=voice_cost,
                    usage_type="voice_failed",
                    character_id=character_id,
                    session_id=message.get("session_id"),
                )
            except Exception as refund_error:
                logger.error(f"Failed to refund credits after message audio failure: {refund_error}")
        elif credits_deducted and guest_state is not None and guest_original_credits is not None:
            guest_state["credits_remaining"] = guest_original_credits
            guest_state["updated_at"] = int(time.time())
        raise


@router.get("/gallery/{character_id}")
async def get_character_gallery(
    request: Request, 
    character_id: str,
    media_type: str = "all",
    limit: int = 200,
) -> list[dict[str, Any]]:
    user_id = _get_user_id(request)
    safe_limit = max(1, min(limit, 500))
    normalized_media_type = str(media_type or "all").lower()

    query = """
        SELECT
            m.id,
            m.session_id,
            m.character_id,
            m.content,
            m.message_type,
            m.image_urls,
            m.metadata,
            m.created_at,
            COALESCE(c.first_name, c.name) AS character_name,
            c.profile_image_url AS character_image_url
        FROM chat_messages m
        LEFT JOIN characters c ON c.id = m.character_id
        WHERE m.user_id = ?
          AND m.character_id = ?
          AND m.message_type IN ('image', 'video')
    """
    params: list[Any] = [user_id, character_id]
    if normalized_media_type in {"image", "video"}:
        query += " AND m.message_type = ?"
        params.append(normalized_media_type)
    query += " ORDER BY m.created_at DESC LIMIT ?"
    params.append(safe_limit)

    rows = await db.execute(query, tuple(params), fetch_all=True)
    items: list[dict[str, Any]] = []
    for row in rows or []:
        image_urls_raw = row.get("image_urls")
        image_urls: list[str] = []
        if isinstance(image_urls_raw, str) and image_urls_raw:
            try:
                parsed = json.loads(image_urls_raw)
                if isinstance(parsed, list):
                    image_urls = [str(url).strip() for url in parsed if str(url).strip()]
            except json.JSONDecodeError:
                image_urls = []
        elif isinstance(image_urls_raw, list):
            image_urls = [str(url).strip() for url in image_urls_raw if str(url).strip()]

        metadata_raw = row.get("metadata")
        metadata: dict[str, Any] = {}
        if isinstance(metadata_raw, str) and metadata_raw:
            try:
                parsed = json.loads(metadata_raw)
                if isinstance(parsed, dict):
                    metadata = parsed
            except json.JSONDecodeError:
                metadata = {}
        elif isinstance(metadata_raw, dict):
            metadata = metadata_raw

        video_url = str(metadata.get("video_url") or "").strip() if isinstance(metadata, dict) else ""
        image_url = image_urls[0] if image_urls else None

        if str(row.get("message_type") or "").lower() == "video" and not video_url:
            continue
        if str(row.get("message_type") or "").lower() == "image" and not image_url:
            continue

        items.append(
            {
                "id": row.get("id"),
                "session_id": row.get("session_id"),
                "character_id": row.get("character_id"),
                "character_name": row.get("character_name"),
                "character_image_url": row.get("character_image_url"),
                "content": row.get("content"),
                "image_url": image_url,
                "video_url": video_url or None,
                "created_at": row.get("created_at"),
            }
        )
    return items


@router.get("/gallery")
async def get_gallery(
    request: Request,
    media_type: str = "all",
    limit: int = 200,
) -> list[dict[str, Any]]:
    user_id = _get_user_id(request)
    safe_limit = max(1, min(limit, 500))
    normalized_media_type = str(media_type or "all").lower()

    query = """
        SELECT
            m.id,
            m.session_id,
            m.character_id,
            m.content,
            m.message_type,
            m.image_urls,
            m.metadata,
            m.created_at,
            COALESCE(c.first_name, c.name) AS character_name,
            c.profile_image_url AS character_image_url
        FROM chat_messages m
        LEFT JOIN characters c ON c.id = m.character_id
        WHERE m.user_id = ?
          AND m.message_type IN ('image', 'video')
    """
    params: list[Any] = [user_id]
    if normalized_media_type in {"image", "video"}:
        query += " AND m.message_type = ?"
        params.append(normalized_media_type)
    query += " ORDER BY m.created_at DESC LIMIT ?"
    params.append(safe_limit)

    rows = await db.execute(query, tuple(params), fetch_all=True)
    items: list[dict[str, Any]] = []
    for row in rows or []:
        image_urls_raw = row.get("image_urls")
        image_urls: list[str] = []
        if isinstance(image_urls_raw, str) and image_urls_raw:
            try:
                parsed = json.loads(image_urls_raw)
                if isinstance(parsed, list):
                    image_urls = [str(url).strip() for url in parsed if str(url).strip()]
            except json.JSONDecodeError:
                image_urls = []
        elif isinstance(image_urls_raw, list):
            image_urls = [str(url).strip() for url in image_urls_raw if str(url).strip()]

        metadata_raw = row.get("metadata")
        metadata: dict[str, Any] = {}
        if isinstance(metadata_raw, str) and metadata_raw:
            try:
                parsed = json.loads(metadata_raw)
                if isinstance(parsed, dict):
                    metadata = parsed
            except json.JSONDecodeError:
                metadata = {}
        elif isinstance(metadata_raw, dict):
            metadata = metadata_raw

        video_url = str(metadata.get("video_url") or "").strip() if isinstance(metadata, dict) else ""
        image_url = image_urls[0] if image_urls else None

        if str(row.get("message_type") or "").lower() == "video" and not video_url:
            continue
        if str(row.get("message_type") or "").lower() == "image" and not image_url:
            continue

        items.append(
            {
                "id": row.get("id"),
                "session_id": row.get("session_id"),
                "character_id": row.get("character_id"),
                "character_name": row.get("character_name"),
                "character_image_url": row.get("character_image_url"),
                "content": row.get("content"),
                "image_url": image_url,
                "video_url": video_url or None,
                "created_at": row.get("created_at"),
            }
        )
    return items


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
