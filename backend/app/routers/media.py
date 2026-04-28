import logging
import asyncio
import random
import json
import uuid
import time
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any, Optional
from pydantic import BaseModel, Field
import httpx

from app.models import BaseResponse, Task, TaskStatus
from app.services.media import NovitaImageProvider, LoRAConfig, IPAdapterConfig, ControlNetConfig
from app.services.media_service import MediaService
from app.services.character_service import character_service
from app.config import get_lora_config, NEGATIVE_PROMPTS
from app.services.credit_service import credit_service, InsufficientCreditsError
from app.core.dependencies import get_firebase_service
from app.services.auth_service import jwt_service
from app.core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["media"])

media_service = MediaService.get_instance()
IMAGE_TASK_CONTEXT_TTL_SECONDS = 60 * 60 * 6
IMAGE_TASK_CONTEXT_KEY_PREFIX = "chat_media_task:"
LEGACY_IMAGE_TASK_CONTEXT_KEY_PREFIX = "chat_image_task:"


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


async def _deduct_guest_credits_for_usage(request: Request, usage_type: str) -> float:
    from app.routers import chat as chat_router

    guest_id = chat_router._resolve_guest_id(request)
    state = chat_router._get_guest_state(guest_id)
    config = await credit_service.get_config()
    amount_map = {
        "voice": float(config.get("voice_cost", 0)),
        "image": float(config.get("image_cost", 0)),
        "video": float(config.get("video_cost", 0)),
        "voice_call": float(config.get("voice_call_per_minute", 0)),
    }
    amount = float(amount_map.get(usage_type, 0))
    credits_remaining = float(state.get("credits_remaining", chat_router.GUEST_MAX_CREDITS))
    if credits_remaining < amount:
        raise HTTPException(
            status_code=402,
            detail={
                "error_code": "guest_credits_exhausted",
                "message": "Guest credits exhausted. Please register to continue.",
                "available": credits_remaining,
                "required": amount,
            },
        )
    state["credits_remaining"] = max(0.0, credits_remaining - amount)
    state["updated_at"] = int(time.time())
    return amount


def _pick_random_template(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    candidates = [
        part.strip()
        for line in text.splitlines()
        for part in line.split("||")
        if part.strip()
    ]
    if not candidates:
        return ""
    return random.choice(candidates)


def _split_trigger_actions(raw: str) -> list[str]:
    parts = [part.strip() for part in (raw or "").split(",")]
    return [part for part in parts if part]


async def _resolve_lora_preset(
    lora_preset_id: Optional[str],
    *,
    context: str = "",
    applies_to: str = "img2img",
) -> tuple[list[LoRAConfig], dict[str, str]]:
    """Return (lora_configs, prompt_hints) for the given preset id.

    When lora_preset_id is None the LLM selector picks one automatically using
    the prompt text as context.  Raises HTTPException 404 only when a specific
    id is given but does not exist or is disabled.
    """
    def _prompt_hints_from_row(row: dict[str, Any]) -> dict[str, str]:
        return {
            "trigger_word": row.get("trigger_word") or "",
            "example_prompt": row.get("example_prompt") or "",
            "example_negative_prompt": row.get("example_negative_prompt") or "",
            "prompt_template_mode": row.get("prompt_template_mode") or "append_trigger",
        }

    if not lora_preset_id:
        from app.services.lora_selector_service import select_lora
        chosen = await select_lora(context=context, applies_to=applies_to)
        if not chosen:
            return [], {}
        lora_cfg = LoRAConfig(model_name=chosen["model_name"], strength=float(chosen["strength"]))
        return [lora_cfg], _prompt_hints_from_row(chosen)

    row = await db.execute(
        "SELECT * FROM lora_presets WHERE id = ? AND is_active = 1",
        (lora_preset_id,),
        fetch=True,
    )
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"LoRA preset '{lora_preset_id}' not found or is disabled",
        )
    lora_cfg = LoRAConfig(model_name=row["model_name"], strength=float(row["strength"]))
    return [lora_cfg], _prompt_hints_from_row(dict(row))


def _compose_prompt_with_lora(base_prompt: str, prompt_hints: dict[str, str]) -> str:
    mode = prompt_hints.get("prompt_template_mode") or "append_trigger"
    trigger_word = prompt_hints.get("trigger_word") or ""
    example_prompt = _pick_random_template(prompt_hints.get("example_prompt") or "")

    if mode == "use_example" and example_prompt:
        return f"{example_prompt}, {base_prompt}"
    if trigger_word:
        return f"{trigger_word}, {base_prompt}"
    return base_prompt


def _get_user_id(request: Request) -> str:
    return getattr(request.state, "user_id", "guest")


def _get_user_db_id(request: Request) -> Optional[str]:
    return getattr(request.state, "user_db_id", None)


async def deduct_credits_for_usage(
    user_id: str,
    usage_type: str,
    amount: Optional[float] = None,
    character_id: Optional[str] = None,
    session_id: Optional[str] = None,
) -> float:
    """
    Deduct credits for a usage.
    Returns the amount deducted.
    Raises HTTPException if insufficient credits.
    """
    config = await credit_service.get_config()
    
    if amount is None:
        amount_map = {
            "voice": config["voice_cost"],
            "image": config["image_cost"],
            "video": config["video_cost"],
            "voice_call": config["voice_call_per_minute"],
        }
        amount = amount_map.get(usage_type, 0)
    
    balance = await credit_service.get_balance(user_id)
    if balance["total"] < amount:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You have {balance['total']} credits, need {amount} for {usage_type}."
        )
    
    try:
        await credit_service.deduct_credits(
            user_id=user_id,
            amount=amount,
            usage_type=usage_type,
            character_id=character_id,
            session_id=session_id,
        )
        return amount
    except InsufficientCreditsError as e:
        raise HTTPException(status_code=402, detail=str(e))


class GenerateMatureLoRARequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2048)
    character_id: Optional[str] = None
    session_id: Optional[str] = None
    lora_id: Optional[str] = None          # legacy: trigger-word preset from lora_configs.py
    lora_preset_id: Optional[str] = None   # new: db-managed LoRA with model path
    width: int = Field(default=1024, ge=128, le=2048)
    height: int = Field(default=1024, ge=128, le=2048)
    steps: int = Field(default=20, ge=1, le=100)
    guidance_scale: float = Field(default=6.0, ge=1.0, le=30.0)
    strength: float = Field(default=0.45, ge=0.0, le=1.0)
    negative_prompt: Optional[str] = None


class GeneratePoseMatureRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2048)
    character_id: Optional[str] = None
    session_id: Optional[str] = None
    lora_id: Optional[str] = None
    lora_preset_id: Optional[str] = None
    pose_image_url: str = Field(..., min_length=1)
    width: int = Field(default=1024, ge=128, le=2048)
    height: int = Field(default=1024, ge=128, le=2048)
    steps: int = Field(default=20, ge=1, le=100)
    guidance_scale: float = Field(default=6.0, ge=1.0, le=30.0)
    strength: float = Field(default=0.45, ge=0.0, le=1.0)
    ip_adapter_strength: float = Field(default=0.45, ge=0.0, le=1.0)
    controlnet_strength: float = Field(default=0.65, ge=0.0, le=1.0)
    negative_prompt: Optional[str] = None


class GenerateWithFaceRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2048)
    face_image_url: str = Field(..., min_length=1)
    character_id: Optional[str] = None
    width: int = Field(default=512, ge=128, le=1024)
    height: int = Field(default=768, ge=128, le=1024)
    ip_adapter_strength: float = Field(default=0.8, ge=0.0, le=1.0)
    steps: int = Field(default=25, ge=1, le=100)
    negative_prompt: Optional[str] = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    raw_status: Optional[str] = None
    progress: float = 0.0
    image_url: Optional[str] = None
    result: Optional[dict[str, Optional[str]]] = None
    error: Optional[str] = None


def _normalize_task_status(raw_status: str) -> str:
    status = (raw_status or "").upper()
    if status == "TASK_STATUS_SUCCEED":
        return "succeeded"
    if status == "TASK_STATUS_FAILED":
        return "failed"
    if status in {"TASK_STATUS_RUNNING", "TASK_STATUS_PROCESSING"}:
        return "processing"
    if status in {"TASK_STATUS_QUEUED", "TASK_STATUS_PENDING"}:
        return "pending"
    return "processing"


def _image_task_context_key(task_id: str) -> str:
    return f"{IMAGE_TASK_CONTEXT_KEY_PREFIX}{task_id}"


async def _cache_image_task_context(
    task_id: str,
    session_id: Optional[str],
    character_id: Optional[str],
    user_id: Optional[str],
    media_type: str = "image",
    extra: Optional[dict[str, Any]] = None,
) -> None:
    if not task_id or not user_id:
        return

    from app.core.redis_client import redis_client

    payload: dict[str, Any] = {
        "task_id": task_id,
        "user_id": user_id,
        "media_type": media_type,
    }
    if session_id:
        payload["session_id"] = session_id
    if character_id:
        payload["character_id"] = character_id
    if extra:
        payload.update(extra)

    await redis_client.set_json(
        _image_task_context_key(task_id),
        payload,
        ex=IMAGE_TASK_CONTEXT_TTL_SECONDS,
    )


async def _get_image_task_context(task_id: str) -> Optional[dict[str, str]]:
    if not task_id:
        return None
    from app.core.redis_client import redis_client
    context = await redis_client.get_json(_image_task_context_key(task_id))
    if context is None:
        context = await redis_client.get_json(f"{LEGACY_IMAGE_TASK_CONTEXT_KEY_PREFIX}{task_id}")
    return context if isinstance(context, dict) else None


async def _clear_image_task_context(task_id: str) -> None:
    if not task_id:
        return
    from app.core.redis_client import redis_client
    await redis_client.delete(_image_task_context_key(task_id))
    await redis_client.delete(f"{LEGACY_IMAGE_TASK_CONTEXT_KEY_PREFIX}{task_id}")


async def _update_image_task_context(task_id: str, updates: dict[str, Any]) -> None:
    if not task_id or not updates:
        return
    from app.core.redis_client import redis_client
    existing = await _get_image_task_context(task_id) or {}
    existing.update(updates)
    await redis_client.set_json(
        _image_task_context_key(task_id),
        existing,
        ex=IMAGE_TASK_CONTEXT_TTL_SECONDS,
    )


async def _persist_generated_image_message(
    task_id: str,
    media_url: str,
    task_context: Optional[dict[str, str]],
    media_type: str = "image",
) -> None:
    if not task_context:
        return

    session_id = str(task_context.get("session_id") or "").strip()
    character_id = str(task_context.get("character_id") or "").strip()
    user_id = str(task_context.get("user_id") or "").strip()
    if not session_id or not character_id or not user_id:
        return

    now = datetime.utcnow().isoformat()
    normalized_media_type = "video" if media_type == "video" else "image"
    metadata_payload: dict[str, Any] = {
        "source": "novita_callback",
        "task_id": task_id,
    }
    image_urls: list[str] = []
    if normalized_media_type == "image":
        image_urls = [media_url] if media_url else []
    else:
        metadata_payload["video_url"] = media_url

    metadata = json.dumps(metadata_payload)
    image_urls_json = json.dumps(image_urls)

    existing = await db.execute(
        "SELECT id FROM chat_messages WHERE id = ?",
        (task_id,),
        fetch=True,
    )

    if existing:
        await db.execute(
            """UPDATE chat_messages
               SET content = ?, message_type = ?, image_urls = ?, metadata = ?
               WHERE id = ?""",
            ("", normalized_media_type, image_urls_json, metadata, task_id),
        )
    else:
        await db.execute(
            """INSERT INTO chat_messages
               (id, session_id, role, content, character_id, user_id, message_type, image_urls, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task_id,
                session_id,
                "assistant",
                "",
                character_id,
                user_id,
                normalized_media_type,
                image_urls_json,
                metadata,
                now,
            ),
        )

    await db.execute(
        "UPDATE chat_sessions SET last_message_at = ?, updated_at = ? WHERE id = ?",
        (now, now, session_id),
    )


@router.post("/generate-mature-lora")
async def generate_mature_lora(
    request: Request,
    data: GenerateMatureLoRARequest,
) -> dict[str, Any]:
    authenticated_user_id = _resolve_authenticated_user_id(request)
    user_id = authenticated_user_id or _get_user_id(request)
    user_db_id = authenticated_user_id or _get_user_db_id(request)

    # Resolve LoRA preset before charging credits so a bad id fails fast (no charge).
    lora_configs, prompt_hints = await _resolve_lora_preset(
        data.lora_preset_id, context=data.prompt, applies_to="img2img"
    )

    if user_db_id and user_id != "guest":
        await deduct_credits_for_usage(
            user_id=user_db_id,
            usage_type="image",
            character_id=data.character_id,
            session_id=data.session_id,
        )
    else:
        await _deduct_guest_credits_for_usage(request, "image")

    provider = media_service.get_image_provider("novita")

    if not provider or not isinstance(provider, NovitaImageProvider):
        raise HTTPException(status_code=503, detail="Novita image provider not available")

    prompt = data.prompt

    # db-managed LoRA preset takes priority; fall back to legacy trigger-word preset
    if prompt_hints:
        prompt = _compose_prompt_with_lora(prompt, prompt_hints)
    elif data.lora_id:
        legacy = get_lora_config(data.lora_id)
        if legacy:
            prompt = f"{legacy.trigger_word}, {prompt}"

    negative_prompt = data.negative_prompt or NEGATIVE_PROMPTS["default"]
    if prompt_hints:
        mode = prompt_hints.get("prompt_template_mode") or "append_trigger"
        example_negative = _pick_random_template(
            prompt_hints.get("example_negative_prompt") or ""
        )
        if mode == "use_example" and example_negative:
            negative_prompt = f"{example_negative}, {negative_prompt}"

    try:
        task_id: Optional[str] = None
        base_image_url: Optional[str] = None

        face_reference_url: Optional[str] = None
        if data.character_id:
            try:
                character = await character_service.get_character_by_id(data.character_id)
                if character:
                    base_image_url = (
                        character.get("mature_image_url")
                        or character.get("avatar_url")
                        or character.get("profile_image_url")
                        or character.get("cover_url")
                    )
                    face_reference_url = (
                        character.get("avatar_url")
                        or character.get("profile_image_url")
                        or character.get("mature_image_url")
                        or character.get("cover_url")
                    )
            except Exception as e:
                logger.warning("Failed to resolve character base image for %s: %s", data.character_id, e)

        # Align with batch character generation path:
        # prefer img2img with character image, then fallback to txt2img.
        if base_image_url:
            try:
                task_id = await provider.img2img_async(
                    init_image_url=base_image_url,
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=data.width,
                    height=data.height,
                    steps=data.steps,
                    guidance_scale=data.guidance_scale,
                    strength=data.strength,
                    loras=lora_configs if lora_configs else None,
                )
            except Exception as e:
                logger.warning(
                    "img2img submit failed for character %s, fallback to txt2img: %s",
                    data.character_id,
                    e,
                )

        if not task_id:
            task_id = await provider.txt2img_async(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=data.width,
                height=data.height,
                steps=data.steps,
                guidance_scale=data.guidance_scale,
                loras=lora_configs if lora_configs else None,
                restore_faces=True,
            )

        await _cache_image_task_context(
            task_id=task_id,
            session_id=data.session_id,
            character_id=data.character_id,
            user_id=user_id,
            media_type="image",
            extra={
                "face_reference_url": face_reference_url,
                "merge_face_enabled": True,
            },
        )
        
        return {
            "task_id": task_id,
            "status": "TASK_STATUS_QUEUED",
            "character_id": data.character_id,
            "session_id": data.session_id,
        }
    
    except Exception as e:
        logger.error(f"Failed to submit image generation task: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/generate-pose-mature")
async def generate_pose_mature(
    request: Request,
    data: GeneratePoseMatureRequest,
) -> dict[str, Any]:
    authenticated_user_id = _resolve_authenticated_user_id(request)
    user_id = authenticated_user_id or _get_user_id(request)
    user_db_id = authenticated_user_id or _get_user_db_id(request)

    # Resolve LoRA preset before charging credits so a bad id fails fast (no charge).
    lora_configs, prompt_hints = await _resolve_lora_preset(
        data.lora_preset_id, context=data.prompt, applies_to="img2img"
    )

    if user_db_id and user_id != "guest":
        await deduct_credits_for_usage(
            user_id=user_db_id,
            usage_type="image",
            character_id=data.character_id,
            session_id=data.session_id,
        )
    else:
        await _deduct_guest_credits_for_usage(request, "image")

    provider = media_service.get_image_provider("novita")

    if not provider or not isinstance(provider, NovitaImageProvider):
        raise HTTPException(status_code=503, detail="Novita image provider not available")

    prompt = data.prompt
    if prompt_hints:
        prompt = _compose_prompt_with_lora(prompt, prompt_hints)
    elif data.lora_id:
        legacy = get_lora_config(data.lora_id)
        if legacy:
            prompt = f"{legacy.trigger_word}, {prompt}"
    negative_prompt = data.negative_prompt or NEGATIVE_PROMPTS["realistic"]
    if prompt_hints:
        mode = prompt_hints.get("prompt_template_mode") or "append_trigger"
        example_negative = _pick_random_template(
            prompt_hints.get("example_negative_prompt") or ""
        )
        if mode == "use_example" and example_negative:
            negative_prompt = f"{example_negative}, {negative_prompt}"

    try:
        base_image_url: Optional[str] = None
        face_reference_url: Optional[str] = None
        if data.character_id:
            try:
                character = await character_service.get_character_by_id(data.character_id)
                if character:
                    base_image_url = (
                        character.get("mature_image_url")
                        or character.get("avatar_url")
                        or character.get("profile_image_url")
                        or character.get("cover_url")
                    )
                    face_reference_url = (
                        character.get("avatar_url")
                        or character.get("profile_image_url")
                        or character.get("mature_image_url")
                        or character.get("cover_url")
                    )
            except Exception as e:
                logger.warning("Failed to resolve face reference for %s: %s", data.character_id, e)

        pose_image_base64 = await provider._download_image_base64(data.pose_image_url)
        face_base64 = None
        if face_reference_url:
            try:
                face_base64 = await provider._download_image_base64(face_reference_url)
            except Exception as e:
                logger.warning("Failed to resolve IPAdapter reference for %s: %s", data.character_id, e)
        
        controlnet = ControlNetConfig(
            model_name="controlnet-openpose-sdxl-1.0",
            image_base64=pose_image_base64,
            strength=data.controlnet_strength,
            preprocessor="openpose",
            guidance_start=0.0,
            guidance_end=1.0,
        )

        ip_adapters = [
            IPAdapterConfig(image_base64=face_base64, strength=data.ip_adapter_strength)
        ] if face_base64 else None
        
        task_id = await provider.img2img_async(
            init_image_url=base_image_url or data.pose_image_url,
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=data.width,
            height=data.height,
            steps=data.steps,
            guidance_scale=data.guidance_scale,
            strength=data.strength,
            controlnet=controlnet,
            ip_adapters=ip_adapters,
            loras=lora_configs if lora_configs else None,
        )

        await _cache_image_task_context(
            task_id=task_id,
            session_id=data.session_id,
            character_id=data.character_id,
            user_id=user_id,
            media_type="image",
            extra={
                "face_reference_url": face_reference_url,
                "merge_face_enabled": True,
            },
        )
        
        return {
            "task_id": task_id,
            "status": "TASK_STATUS_QUEUED",
            "character_id": data.character_id,
            "session_id": data.session_id,
        }
    
    except Exception as e:
        logger.error(f"Failed to submit pose image generation task: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/generate-with-face")
async def generate_with_face(
    request: Request,
    data: GenerateWithFaceRequest,
) -> dict[str, Any]:
    authenticated_user_id = _resolve_authenticated_user_id(request)
    user_id = authenticated_user_id or _get_user_id(request)
    user_db_id = authenticated_user_id or _get_user_db_id(request)
    
    if user_db_id and user_id != "guest":
        await deduct_credits_for_usage(
            user_id=user_db_id,
            usage_type="image",
            character_id=data.character_id,
        )
    else:
        await _deduct_guest_credits_for_usage(request, "image")
    
    provider = media_service.get_image_provider("novita")
    
    if not provider or not isinstance(provider, NovitaImageProvider):
        raise HTTPException(status_code=503, detail="Novita image provider not available")
    
    negative_prompt = data.negative_prompt or NEGATIVE_PROMPTS["realistic"]
    
    try:
        task_id = await provider.generate_with_ip_adapter(
            prompt=data.prompt,
            face_image_url=data.face_image_url,
            negative_prompt=negative_prompt,
            width=data.width,
            height=data.height,
            ip_adapter_strength=data.ip_adapter_strength,
            steps=data.steps,
        )
        
        return {
            "task_id": task_id,
            "status": "TASK_STATUS_QUEUED",
            "character_id": data.character_id,
        }
    
    except Exception as e:
        logger.error(f"Failed to submit face image generation task: {e}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    request: Request,
    task_id: str,
) -> TaskStatusResponse:
    provider = media_service.get_image_provider("novita")
    
    if not provider or not isinstance(provider, NovitaImageProvider):
        raise HTTPException(status_code=503, detail="Novita image provider not available")
    
    try:
        result = await provider.get_task_result(task_id)
        normalized_status = _normalize_task_status(result.status)
        result_payload: dict[str, Optional[str]] = {}
        if result.image_url:
            task_context = await _get_image_task_context(task_id)
            if task_context:
                merge_enabled = bool(task_context.get("merge_face_enabled"))
                face_reference_url = str(task_context.get("face_reference_url") or "").strip()
                cached_merged_url = str(task_context.get("merged_image_url") or "").strip()
                merge_failed = bool(task_context.get("merge_face_failed"))

                if cached_merged_url:
                    result.image_url = cached_merged_url
                elif (
                    merge_enabled
                    and face_reference_url
                    and not merge_failed
                ):
                    try:
                        merged_image_url = await provider.merge_face(
                            image_url=result.image_url,
                            face_image_url=face_reference_url,
                        )
                        if merged_image_url:
                            result.image_url = merged_image_url
                            await _update_image_task_context(
                                task_id,
                                {
                                    "merged_image_url": merged_image_url,
                                    "merge_face_done": True,
                                },
                            )
                    except Exception as e:
                        logger.warning("merge-face failed for task %s: %s", task_id, e)
                        await _update_image_task_context(
                            task_id,
                            {
                                "merge_face_failed": True,
                                "merge_face_error": str(e),
                            },
                        )

            result_payload["data"] = result.image_url
            result_payload["image_url"] = result.image_url
            if task_context:
                await _persist_generated_image_message(
                    task_id,
                    result.image_url,
                    task_context,
                    media_type="image",
                )
        if result.video_url:
            result_payload["video_url"] = result.video_url
            result_payload.setdefault("data", result.video_url)
            task_context = await _get_image_task_context(task_id)
            if task_context:
                await _persist_generated_image_message(
                    task_id,
                    result.video_url,
                    task_context,
                    media_type="video",
                )
        if normalized_status in {"succeeded", "failed"}:
            await _clear_image_task_context(task_id)
        
        return TaskStatusResponse(
            task_id=result.task_id,
            status=normalized_status,
            raw_status=result.status,
            progress=result.progress,
            image_url=result.image_url,
            result=result_payload or None,
            error=result.error,
        )

    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        if status_code in (403, 404):
            raise HTTPException(status_code=status_code, detail="Task not accessible") from e
        logger.warning("Transient HTTP status while getting task status %s: %s", task_id, e)
        return TaskStatusResponse(
            task_id=task_id,
            status="processing",
            raw_status="TRANSIENT_HTTP_ERROR",
            progress=0.0,
        )
    except httpx.RequestError as e:
        logger.warning("Transient network error while getting task status %s: %s", task_id, e)
        return TaskStatusResponse(
            task_id=task_id,
            status="processing",
            raw_status="TRANSIENT_NETWORK_ERROR",
            progress=0.0,
        )
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.post("/save-media")
async def save_media(request: Request, data: dict[str, Any]) -> BaseResponse:
    user_id = _get_user_id(request)
    character_id = str(data.get("character_id") or "").strip() or None
    character_name = str(data.get("character_name") or "").strip()
    prompt = str(data.get("prompt") or "").strip()
    task_id = str(data.get("task_id") or "").strip() or None

    image_urls_raw = data.get("image_urls")
    image_urls: list[str] = []
    if isinstance(image_urls_raw, list):
        image_urls = [str(url).strip() for url in image_urls_raw if str(url).strip()]
    elif isinstance(image_urls_raw, str) and image_urls_raw.strip():
        image_urls = [image_urls_raw.strip()]

    video_url = str(data.get("video_url") or "").strip()
    video_urls_raw = data.get("video_urls")
    video_urls: list[str] = []
    if video_url:
        video_urls.append(video_url)
    if isinstance(video_urls_raw, list):
        video_urls.extend(str(url).strip() for url in video_urls_raw if str(url).strip())
    elif isinstance(video_urls_raw, str) and video_urls_raw.strip():
        video_urls.append(video_urls_raw.strip())

    if not image_urls and not video_urls:
        return BaseResponse(success=True, message="No media to save")

    if character_id and not character_name:
        row = await db.execute(
            "SELECT first_name, name FROM characters WHERE id = ?",
            (character_id,),
            fetch=True,
        )
        if row:
            character_name = str(row.get("first_name") or row.get("name") or "").strip()

    metadata = json.dumps(
        {
            "prompt": prompt,
            "character_id": character_id,
            "character_name": character_name,
            "source": "collection_save_media",
        }
    )
    now = datetime.utcnow().isoformat()

    for image_url in image_urls:
        await db.execute(
            """INSERT INTO media_assets (id, user_id, task_id, type, url, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                f"media_{uuid.uuid4().hex}",
                user_id,
                task_id,
                "image",
                image_url,
                metadata,
                now,
            ),
        )

    for saved_video_url in video_urls:
        await db.execute(
            """INSERT INTO media_assets (id, user_id, task_id, type, url, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                f"media_{uuid.uuid4().hex}",
                user_id,
                task_id,
                "video",
                saved_video_url,
                metadata,
                now,
            ),
        )

    return BaseResponse(success=True, message="Media saved")


@router.get("/video-lora-actions")
async def list_video_lora_actions(request: Request) -> dict[str, Any]:
    rows = await db.execute(
        """
        SELECT id, name, trigger_word, example_prompt, description
        FROM lora_presets
        WHERE is_active = 1
          AND provider = 'novita'
          AND (applies_to = 'video' OR applies_to = 'all')
        ORDER BY created_at DESC
        """,
        fetch_all=True,
    )

    actions: list[dict[str, str]] = []
    for row in rows or []:
        item = dict(row)
        lora_id = str(item.get("id") or "")
        lora_name = str(item.get("name") or "")
        description = str(item.get("description") or "")
        example_prompt = item.get("example_prompt") or ""

        triggers = _split_trigger_actions(item.get("trigger_word") or "")
        if not triggers:
            continue

        for idx, trigger in enumerate(triggers):
            default_prompt = _pick_random_template(example_prompt) or trigger
            action_id = f"{lora_id}:{idx}"
            actions.append(
                {
                    "id": action_id,
                    "lora_preset_id": lora_id,
                    "lora_name": lora_name,
                    "action_label": trigger,
                    "trigger_word": trigger,
                    "default_prompt": default_prompt,
                    "description": description,
                }
            )

    return {"actions": actions}


@router.post("/generate-video-wan-character")
async def generate_video_wan_character(
    request: Request,
    data: dict[str, Any],
) -> dict[str, Any]:
    authenticated_user_id = _resolve_authenticated_user_id(request)
    user_id = authenticated_user_id or _get_user_id(request)
    user_db_id = authenticated_user_id or _get_user_db_id(request)
    provider = media_service.get_video_provider("novita")

    if not provider:
        raise HTTPException(status_code=503, detail="Video provider not available")

    prompt = data.get("prompt", "")
    lora_preset_id = data.get("lora_preset_id")
    selected_trigger_word = (data.get("selected_trigger_word") or "").strip()
    _, prompt_hints = await _resolve_lora_preset(
        lora_preset_id, context=prompt, applies_to="video"
    )
    if prompt_hints:
        if selected_trigger_word:
            prompt_hints = {**prompt_hints, "trigger_word": selected_trigger_word}
        prompt = _compose_prompt_with_lora(prompt, prompt_hints)

    if user_db_id and user_id != "guest":
        await deduct_credits_for_usage(
            user_id=user_db_id,
            usage_type="video",
            character_id=data.get("character_id"),
            session_id=data.get("session_id"),
        )
    else:
        await _deduct_guest_credits_for_usage(request, "video")

    try:
        from app.services.media import NovitaVideoProvider
        if isinstance(provider, NovitaVideoProvider):
            task_id = await provider.generate_video_async(
                prompt=prompt,
                init_image=data.get("image_url"),
            )

            await _cache_image_task_context(
                task_id=task_id,
                session_id=data.get("session_id"),
                character_id=data.get("character_id"),
                user_id=user_id,
                media_type="video",
            )
            
            return {
                "task_id": task_id,
                "status": "TASK_STATUS_QUEUED",
                "character_id": data.get("character_id"),
                "session_id": data.get("session_id"),
            }
        else:
            raise HTTPException(status_code=503, detail="Invalid video provider")
    
    except Exception as e:
        logger.error(f"Failed to submit video generation task: {e}")
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")


@router.post("/animate-standalone")
async def animate_standalone(
    request: Request,
    data: dict[str, Any],
) -> dict[str, Any]:
    authenticated_user_id = _resolve_authenticated_user_id(request)
    user_id = authenticated_user_id or _get_user_id(request)
    user_db_id = authenticated_user_id or _get_user_db_id(request)
    
    image_url = data.get("image_url")
    prompt = data.get("prompt")
    character_id = data.get("character_id")
    
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")
    
    provider = media_service.get_video_provider("novita")
    
    if not provider:
        raise HTTPException(status_code=503, detail="Video provider not available")

    if user_db_id and user_id != "guest":
        await deduct_credits_for_usage(
            user_id=user_db_id,
            usage_type="video",
            character_id=character_id,
        )
    else:
        await _deduct_guest_credits_for_usage(request, "video")
    
    try:
        from app.services.media import NovitaVideoProvider
        if isinstance(provider, NovitaVideoProvider):
            task_id = await provider.generate_video_async(
                prompt=prompt or "",
                init_image=image_url,
            )
            
            return {
                "task_id": task_id,
                "status": "TASK_STATUS_QUEUED",
                "character_id": character_id,
            }
        else:
            raise HTTPException(status_code=503, detail="Invalid video provider")
    
    except Exception as e:
        logger.error(f"Failed to submit animation task: {e}")
        raise HTTPException(status_code=500, detail=f"Animation failed: {str(e)}")


@router.post("/generate-async", response_model=Task)
async def generate_image_async(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_img_async",
        type="image_generation",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/generate")
async def generate_image(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "image_url": "https://example.com/generated.png",
        "width": 512,
        "height": 512,
    }


@router.post("/generate-batch", response_model=Task)
async def generate_images_batch(request: Request, data: dict[str, Any]) -> Task:
    novita_provider = media_service.get_image_provider("novita")
    if not novita_provider or not isinstance(novita_provider, NovitaImageProvider):
        raise HTTPException(status_code=503, detail="Novita image provider not available")
    provider = media_service.get_image_provider("z_image_turbo_lora") or novita_provider

    prompt = str(data.get("prompt") or "").strip()
    prompts_raw = data.get("prompts")
    prompts: list[str] = []
    if isinstance(prompts_raw, list):
        prompts = [
            str(item).strip()
            for item in prompts_raw
            if isinstance(item, str) and str(item).strip()
        ]

    try:
        count = int(data.get("count", len(prompts) if prompts else 1))
    except (TypeError, ValueError):
        count = len(prompts) if prompts else 1
    count = max(1, min(count, 8))

    if not prompts:
        if not prompt:
            raise HTTPException(status_code=422, detail="prompt is required")
        prompts = [prompt for _ in range(count)]

    negative_prompt = str(data.get("negative_prompt") or "").strip() or NEGATIVE_PROMPTS["default"]
    try:
        width = int(data.get("width", 1024))
    except (TypeError, ValueError):
        width = 1024
    width = max(128, min(width, 2048))

    try:
        height = int(data.get("height", 1024))
    except (TypeError, ValueError):
        height = 1024
    height = max(128, min(height, 2048))

    try:
        steps = int(data.get("steps", 20))
    except (TypeError, ValueError):
        steps = 20
    steps = max(1, min(steps, 100))

    try:
        guidance_scale = float(data.get("guidance_scale", 7.5))
    except (TypeError, ValueError):
        guidance_scale = 7.5
    guidance_scale = max(1.0, min(guidance_scale, 30.0))

    session_id = str(data.get("session_id") or "").strip() or None
    character_id = str(data.get("character_id") or "").strip() or None
    user_id = _get_user_id(request)
    selected_lora_name: Optional[str] = None
    selected_lora_configs: Optional[list[LoRAConfig]] = None

    try:
        lora_row = await db.execute(
            """
            SELECT model_name, strength
            FROM lora_presets
            WHERE is_active = 1
              AND provider = 'novita'
              AND (applies_to = 'txt2img' OR applies_to = 'all')
            ORDER BY RANDOM()
            LIMIT 1
            """,
            fetch=True,
        )
        if lora_row and lora_row.get("model_name"):
            selected_lora_name = str(lora_row["model_name"])
            selected_lora_configs = [
                LoRAConfig(
                    model_name=selected_lora_name,
                    strength=float(lora_row.get("strength") or 0.85),
                )
            ]
    except Exception as e:
        logger.warning("Failed to select random txt2img LoRA for generate-batch: %s", e)

    async def _submit_one(batch_prompt: str) -> str:
        task_id = await provider.txt2img_async(
            prompt=batch_prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=guidance_scale,
            image_num=1,
            loras=selected_lora_configs,
            restore_faces=True,
        )
        if not task_id:
            raise RuntimeError("Provider returned empty task_id")
        await _cache_image_task_context(
            task_id=task_id,
            session_id=session_id,
            character_id=character_id,
            user_id=user_id,
            media_type="image",
        )
        return task_id

    submit_results = await asyncio.gather(
        *[_submit_one(item_prompt) for item_prompt in prompts],
        return_exceptions=True,
    )

    task_ids: list[str] = []
    errors: list[str] = []
    for result in submit_results:
        if isinstance(result, Exception):
            errors.append(str(result))
        elif isinstance(result, str) and result.strip():
            task_ids.append(result.strip())

    if not task_ids:
        logger.error("generate-batch failed, no task submitted: %s", "; ".join(errors) if errors else "unknown")
        raise HTTPException(status_code=500, detail="Failed to submit image generation tasks")

    return Task(
        id=task_ids[0],
        type="batch_image_generation",
        status=TaskStatus.PENDING,
        result={
            "task_id": task_ids[0],
            "task_ids": task_ids,
            "requested_count": len(prompts),
            "submitted_count": len(task_ids),
            "failed_count": len(prompts) - len(task_ids),
            "provider": "z_image_turbo_lora" if provider is not novita_provider else "novita",
            "lora_model_name": selected_lora_name,
            "errors": errors[:5] if errors else [],
        },
        created_at=datetime.now(),
    )


@router.post("/suggestion-previews", response_model=Task)
async def generate_suggestion_previews(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_suggestions",
        type="suggestion_previews",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/generate-preset")
async def generate_preset_image(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "image_url": "https://example.com/preset.png",
        "preset_name": data.get("preset", "default"),
    }


@router.get("/preset-characters")
async def get_preset_characters(request: Request) -> list[dict[str, Any]]:
    return [
        {"name": "Default", "preset_id": "default"},
        {"name": "Fantasy", "preset_id": "fantasy"},
    ]


@router.get("/generate-preset/{character_name}")
async def get_preset_by_character(request: Request, character_name: str) -> dict[str, Any]:
    return {
        "character_name": character_name,
        "preset": {"style": "default", "parameters": {}},
    }


@router.post("/generate-and-save")
async def generate_and_save(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "image_url": "https://example.com/saved.png",
        "saved": True,
    }


@router.post("/generate-preset-and-save")
async def generate_preset_and_save(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "image_url": "https://example.com/preset-saved.png",
        "saved": True,
    }



@router.get("/my-media")
async def get_my_media(
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
            m.type,
            m.url,
            m.metadata,
            m.created_at,
            c.id AS character_id,
            COALESCE(c.first_name, c.name) AS db_character_name,
            c.profile_image_url AS character_image_url
        FROM media_assets m
        LEFT JOIN characters c ON c.id = json_extract(m.metadata, '$.character_id')
        WHERE m.user_id = ?
    """
    params: list[Any] = [user_id]
    if normalized_media_type in {"image", "video"}:
        query += " AND m.type = ?"
        params.append(normalized_media_type)
    query += " ORDER BY m.created_at DESC LIMIT ?"
    params.append(safe_limit)

    rows = await db.execute(query, tuple(params), fetch_all=True)
    items: list[dict[str, Any]] = []
    for row in rows or []:
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

        entry_type = str(row.get("type") or "").lower()
        url = str(row.get("url") or "").strip()
        if not url:
            continue

        items.append(
            {
                "id": row.get("id"),
                "image_url": url if entry_type == "image" else None,
                "video_url": url if entry_type == "video" else None,
                "created_at": row.get("created_at"),
                "prompt": metadata.get("prompt"),
                "character_id": metadata.get("character_id") or row.get("character_id"),
                "character_name": metadata.get("character_name") or row.get("db_character_name"),
                "character_image_url": row.get("character_image_url"),
            }
        )
    return items


@router.post("/voice/generate_token")
async def generate_voice_token(request: Request) -> dict[str, Any]:
    from app.services.voice_service import VoiceService
    from app.services.voice_call_service import voice_call_service
    
    user_id = _get_user_id(request)
    user_db_id = _get_user_db_id(request)
    
    data = await request.json()
    character_id = data.get("character_id")
    session_id = data.get("session_id")
    
    voice_service = VoiceService()
    
    token_data = await voice_service.generate_voice_token(
        session_id=session_id or f"session_{user_db_id or user_id}",
        user_id=user_db_id or user_id,
        character_id=character_id,
    )
    
    room_name = token_data.get("room_name") or token_data.get("room")
    
    if room_name and user_db_id:
        await voice_call_service.start_call(
            room_name=room_name,
            user_id=user_db_id,
            character_id=character_id,
            session_id=session_id,
        )
    
    return token_data


@router.post("/voice/messages/{message_id}/audio", response_model=Task)
async def generate_message_audio(request: Request, message_id: str) -> Task:
    authenticated_user_id = _resolve_authenticated_user_id(request)
    user_id = authenticated_user_id or _get_user_id(request)
    user_db_id = authenticated_user_id or _get_user_db_id(request)
    
    if user_db_id and user_id != "guest":
        await deduct_credits_for_usage(
            user_id=user_db_id,
            usage_type="voice",
        )
    else:
        await _deduct_guest_credits_for_usage(request, "voice")
    
    return Task(
        id="task_voice_msg",
        type="message_audio",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/voice/request-note", response_model=Task)
async def request_voice_note(request: Request, data: dict[str, Any]) -> Task:
    authenticated_user_id = _resolve_authenticated_user_id(request)
    user_id = authenticated_user_id or _get_user_id(request)
    user_db_id = authenticated_user_id or _get_user_db_id(request)
    
    if user_db_id and user_id != "guest":
        await deduct_credits_for_usage(
            user_id=user_db_id,
            usage_type="voice",
            session_id=data.get("session_id"),
        )
    else:
        await _deduct_guest_credits_for_usage(request, "voice")
    
    return Task(
        id="task_voice_note",
        type="voice_note",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.api_route("/voice/ws/{session_id}", methods=["GET", "POST"])
async def voice_websocket(request: Request, session_id: str):
    return {"message": "WebSocket endpoint - use actual WebSocket connection"}


@router.post("/callbacks/novita")
async def novita_callback(request: Request) -> BaseResponse:
    raw_body = await request.json()
    logger.info(f"Novita callback received: {raw_body}")

    event_type = raw_body.get("event_type")
    if event_type and event_type != "ASYNC_TASK_RESULT":
        logger.info("Ignoring Novita callback event_type=%s", event_type)
        return BaseResponse(success=True, message="Novita callback ignored")

    body = raw_body.get("payload") if event_type == "ASYNC_TASK_RESULT" else raw_body
    if not isinstance(body, dict):
        logger.warning("Novita callback payload is not an object: %s", raw_body)
        return BaseResponse(success=True, message="Novita callback received")
    
    task = body.get("task", {})
    if not isinstance(task, dict):
        task = {}
    task_id = body.get("task_id") or task.get("task_id")
    task_status = task.get("status")
    images = body.get("images", [])
    videos = body.get("videos", [])
    
    if task_id:
        from app.core.redis_client import redis_client
        task_context = await _get_image_task_context(task_id)
        task_media_type = str(task_context.get("media_type") or "image") if task_context else "image"

        if task_status == "TASK_STATUS_SUCCEED":
            if images:
                image_url = images[0].get("image_url")
                if image_url:
                    await _persist_generated_image_message(
                        task_id,
                        image_url,
                        task_context,
                        media_type="image",
                    )
                await redis_client.publish(
                    "image_done",
                    json.dumps({
                        "message_id": task_id,
                        "image_url": image_url,
                        "task_id": task_id,
                        "session_id": task_context.get("session_id") if task_context else None,
                    })
                )
            if videos:
                video_url = videos[0].get("video_url")
                if video_url:
                    await _persist_generated_image_message(
                        task_id,
                        video_url,
                        task_context,
                        media_type="video",
                    )
                await redis_client.publish(
                    "video_completed",
                    json.dumps({
                        "task_id": task_id,
                        "message_id": task_id,
                        "session_id": task_context.get("session_id") if task_context else None,
                        "video_url": video_url,
                    })
                )
            await _clear_image_task_context(task_id)
        elif task_status == "TASK_STATUS_FAILED":
            reason = task.get("reason", "Unknown error")
            failure_channel = "video_failed" if task_media_type == "video" else "image_failed"
            await redis_client.publish(
                failure_channel,
                json.dumps({
                    "task_id": task_id,
                    "error": reason,
                    "session_id": task_context.get("session_id") if task_context else None,
                })
            )
            await _clear_image_task_context(task_id)
    
    return BaseResponse(success=True, message="Novita callback received")


@router.post("/callbacks/media")
async def media_callback(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="Media callback received")


@router.get("/callbacks/health")
async def callbacks_health(request: Request) -> dict[str, Any]:
    return {"status": "healthy"}
