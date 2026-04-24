import logging
import random
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Any, Optional
from pydantic import BaseModel, Field

from app.models import BaseResponse, Task, TaskStatus
from app.services.media import NovitaImageProvider, LoRAConfig, ControlNetConfig
from app.services.media_service import MediaService
from app.config import get_lora_config, NEGATIVE_PROMPTS
from app.services.credit_service import credit_service, InsufficientCreditsError
from app.services.pricing_service import pricing_service
from app.core.dependencies import get_current_user_required
from app.core.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/images", tags=["media"])

media_service = MediaService.get_instance()


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
    guidance_scale: float = Field(default=7.5, ge=1.0, le=30.0)
    strength: float = Field(default=0.75, ge=0.0, le=1.0)
    negative_prompt: Optional[str] = None


class GeneratePoseMatureRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=2048)
    character_id: Optional[str] = None
    session_id: Optional[str] = None
    lora_preset_id: Optional[str] = None
    pose_image_url: str = Field(..., min_length=1)
    width: int = Field(default=1024, ge=128, le=2048)
    height: int = Field(default=1024, ge=128, le=2048)
    steps: int = Field(default=20, ge=1, le=100)
    guidance_scale: float = Field(default=7.0, ge=1.0, le=30.0)
    controlnet_strength: float = Field(default=0.7, ge=0.0, le=1.0)
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
    progress: float = 0.0
    image_url: Optional[str] = None
    error: Optional[str] = None


@router.post("/generate-mature-lora")
async def generate_mature_lora(
    request: Request,
    data: GenerateMatureLoRARequest,
) -> dict[str, Any]:
    user_id = _get_user_id(request)
    user_db_id = _get_user_db_id(request)

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
    user_id = _get_user_id(request)
    user_db_id = _get_user_db_id(request)

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

    provider = media_service.get_image_provider("novita")

    if not provider or not isinstance(provider, NovitaImageProvider):
        raise HTTPException(status_code=503, detail="Novita image provider not available")

    prompt = data.prompt
    if prompt_hints:
        prompt = _compose_prompt_with_lora(prompt, prompt_hints)
    negative_prompt = data.negative_prompt or NEGATIVE_PROMPTS["realistic"]
    if prompt_hints:
        mode = prompt_hints.get("prompt_template_mode") or "append_trigger"
        example_negative = _pick_random_template(
            prompt_hints.get("example_negative_prompt") or ""
        )
        if mode == "use_example" and example_negative:
            negative_prompt = f"{example_negative}, {negative_prompt}"

    try:
        pose_image_base64 = await provider._download_image_base64(data.pose_image_url)
        
        controlnet = ControlNetConfig(
            model_name="control_v11p_sd15_openpose",
            image_base64=pose_image_base64,
            strength=data.controlnet_strength,
            preprocessor="openpose",
        )
        
        task_id = await provider.img2img_async(
            init_image_url=data.pose_image_url,
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=data.width,
            height=data.height,
            steps=data.steps,
            guidance_scale=data.guidance_scale,
            strength=1.0,
            controlnet=controlnet,
            loras=lora_configs if lora_configs else None,
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
    user_id = _get_user_id(request)
    user_db_id = _get_user_db_id(request)
    
    if user_db_id and user_id != "guest":
        await deduct_credits_for_usage(
            user_id=user_db_id,
            usage_type="image",
            character_id=data.character_id,
        )
    
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
        
        return TaskStatusResponse(
            task_id=result.task_id,
            status=result.status,
            progress=result.progress,
            image_url=result.image_url,
            error=result.error,
        )
    
    except Exception as e:
        logger.error(f"Failed to get task status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.post("/save-media")
async def save_media(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Media saved")


@router.post("/generate-video-wan-character")
async def generate_video_wan_character(
    request: Request,
    data: dict[str, Any],
) -> dict[str, Any]:
    user_id = _get_user_id(request)
    provider = media_service.get_video_provider("novita")

    if not provider:
        raise HTTPException(status_code=503, detail="Video provider not available")

    prompt = data.get("prompt", "")
    lora_preset_id = data.get("lora_preset_id")
    _, prompt_hints = await _resolve_lora_preset(
        lora_preset_id, context=prompt, applies_to="video"
    )
    if prompt_hints:
        prompt = _compose_prompt_with_lora(prompt, prompt_hints)

    try:
        from app.services.media import NovitaVideoProvider
        if isinstance(provider, NovitaVideoProvider):
            task_id = await provider.generate_video_async(
                prompt=prompt,
                init_image=data.get("image_url"),
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
    user_id = _get_user_id(request)
    
    image_url = data.get("image_url")
    prompt = data.get("prompt")
    character_id = data.get("character_id")
    
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required")
    
    provider = media_service.get_video_provider("novita")
    
    if not provider:
        raise HTTPException(status_code=503, detail="Video provider not available")
    
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
    return Task(
        id="task_img_batch",
        type="batch_image_generation",
        status=TaskStatus.PENDING,
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
async def get_my_media(request: Request) -> list[dict[str, Any]]:
    return [
        {"id": "media_001", "url": "https://example.com/media1.png", "type": "image"},
    ]


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
    user_id = _get_user_id(request)
    user_db_id = _get_user_db_id(request)
    
    if user_db_id and user_id != "guest":
        await deduct_credits_for_usage(
            user_id=user_db_id,
            usage_type="voice",
        )
    
    return Task(
        id="task_voice_msg",
        type="message_audio",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/voice/request-note", response_model=Task)
async def request_voice_note(request: Request, data: dict[str, Any]) -> Task:
    user_id = _get_user_id(request)
    user_db_id = _get_user_db_id(request)
    
    if user_db_id and user_id != "guest":
        await deduct_credits_for_usage(
            user_id=user_db_id,
            usage_type="voice",
            session_id=data.get("session_id"),
        )
    
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
    body = await request.json()
    logger.info(f"Novita callback received: {body}")
    
    task_id = body.get("task_id")
    task = body.get("task", {})
    task_status = task.get("status")
    images = body.get("images", [])
    videos = body.get("videos", [])
    
    if task_id:
        from app.core.redis_client import redis_client
        import json
        
        if task_status == "TASK_STATUS_SUCCEED":
            if images:
                image_url = images[0].get("image_url")
                await redis_client.publish(
                    "image_done",
                    json.dumps({
                        "message_id": task_id,
                        "image_url": image_url,
                        "task_id": task_id,
                    })
                )
            if videos:
                video_url = videos[0].get("video_url")
                await redis_client.publish(
                    "video_completed",
                    json.dumps({
                        "task_id": task_id,
                        "video_url": video_url,
                    })
                )
        elif task_status == "TASK_STATUS_FAILED":
            reason = task.get("reason", "Unknown error")
            await redis_client.publish(
                "image_failed",
                json.dumps({
                    "task_id": task_id,
                    "error": reason,
                })
            )
    
    return BaseResponse(success=True, message="Novita callback received")


@router.post("/callbacks/media")
async def media_callback(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="Media callback received")


@router.get("/callbacks/health")
async def callbacks_health(request: Request) -> dict[str, Any]:
    return {"status": "healthy"}
