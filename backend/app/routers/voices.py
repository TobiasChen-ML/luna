from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field

from app.services.voice_management_service import voice_management_service
from app.core.dependencies import get_current_user_required
from app.models import BaseResponse

router = APIRouter(prefix="/api/voices", tags=["voices"])


class VoiceCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    id: Optional[str] = None
    name: str = Field(..., min_length=1)
    display_name: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None
    provider: str = "elevenlabs"
    provider_voice_id: str = Field(..., min_length=1)
    model_id: Optional[str] = None
    language: str = "en"
    gender: str = "female"
    tone: Optional[str] = None
    settings: dict = Field(default_factory=dict)
    is_active: bool = True


class VoiceUpdate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    preview_url: Optional[str] = None
    provider: Optional[str] = None
    provider_voice_id: Optional[str] = None
    model_id: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    tone: Optional[str] = None
    settings: Optional[dict] = None
    is_active: Optional[bool] = None


class PreviewRequest(BaseModel):
    text: Optional[str] = None


@router.get("")
async def list_voices(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    language: Optional[str] = Query(None, description="Filter by language"),
    gender: Optional[str] = Query(None, description="Filter by gender"),
    tone: Optional[str] = Query(None, description="Filter by tone"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    return await voice_management_service.list_voices(
        provider=provider,
        language=language,
        gender=gender,
        tone=tone,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@router.get("/providers")
async def list_providers() -> list[dict[str, Any]]:
    return [
        {"id": "elevenlabs", "name": "ElevenLabs", "languages": ["en", "multi"]},
        {"id": "dashscope", "name": "通义千问", "languages": ["zh"]},
    ]


@router.get("/tones")
async def list_tones() -> list[dict[str, Any]]:
    return [
        {"id": "warm", "name": "温暖", "name_en": "Warm"},
        {"id": "seductive", "name": "诱惑", "name_en": "Seductive"},
        {"id": "calm", "name": "平静", "name_en": "Calm"},
        {"id": "lively", "name": "活泼", "name_en": "Lively"},
        {"id": "sweet", "name": "甜美", "name_en": "Sweet"},
        {"id": "mature", "name": "成熟", "name_en": "Mature"},
        {"id": "elegant", "name": "优雅", "name_en": "Elegant"},
        {"id": "asmr", "name": "ASMR", "name_en": "ASMR"},
        {"id": "husky", "name": "沙哑", "name_en": "Husky"},
        {"id": "professional", "name": "专业", "name_en": "Professional"},
        {"id": "friendly", "name": "友好", "name_en": "Friendly"},
        {"id": "expressive", "name": "表现力", "name_en": "Expressive"},
    ]


@router.post("/sync/elevenlabs")
async def sync_elevenlabs(
    user: dict = Depends(get_current_user_required),
) -> dict[str, Any]:
    return await voice_management_service.sync_from_elevenlabs()


@router.post("/sync/dashscope")
async def sync_dashscope(
    user: dict = Depends(get_current_user_required),
) -> dict[str, Any]:
    return await voice_management_service.sync_from_dashscope()


@router.get("/{voice_id}")
async def get_voice(voice_id: str) -> dict[str, Any]:
    voice = await voice_management_service.get_voice(voice_id)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


@router.post("")
async def create_voice(
    data: VoiceCreate,
    user: dict = Depends(get_current_user_required),
) -> dict[str, Any]:
    voice = await voice_management_service.create_voice(data.model_dump())
    return voice


@router.patch("/{voice_id}")
async def update_voice(
    voice_id: str,
    data: VoiceUpdate,
    user: dict = Depends(get_current_user_required),
) -> dict[str, Any]:
    voice = await voice_management_service.update_voice(voice_id, data.model_dump(exclude_unset=True))
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


@router.delete("/{voice_id}")
async def delete_voice(
    voice_id: str,
    user: dict = Depends(get_current_user_required),
) -> BaseResponse:
    success = await voice_management_service.delete_voice(voice_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete voice. It may be in use by characters.")
    return BaseResponse(success=True, message="Voice deleted")


@router.post("/{voice_id}/deactivate")
async def deactivate_voice(
    voice_id: str,
    user: dict = Depends(get_current_user_required),
) -> BaseResponse:
    success = await voice_management_service.soft_delete_voice(voice_id)
    if not success:
        raise HTTPException(status_code=404, detail="Voice not found")
    return BaseResponse(success=True, message="Voice deactivated")


@router.post("/{voice_id}/preview")
async def generate_preview(
    voice_id: str,
    data: Optional[PreviewRequest] = None,
) -> dict[str, Any]:
    try:
        result = await voice_management_service.generate_preview(
            voice_id,
            text=data.text if data else None
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@router.post("/{voice_id}/increment-usage")
async def increment_usage(voice_id: str) -> BaseResponse:
    await voice_management_service.increment_usage(voice_id)
    return BaseResponse(success=True, message="Usage incremented")
