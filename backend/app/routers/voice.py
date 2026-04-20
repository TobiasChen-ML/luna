from fastapi import APIRouter, Depends, HTTPException, Header, Request, Body
from typing import Optional
from pydantic import BaseModel
import logging
import json

from ..services.voice_service import VoiceService
from ..services.voice_call_service import voice_call_service
from ..services.credit_service import credit_service
from ..models.schemas import BaseResponse
from ..core.config import get_config_value, settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

voice_service = VoiceService()


class GenerateTokenRequest(BaseModel):
    character_id: Optional[str] = None
    session_id: Optional[str] = None


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    from ..services import FirebaseService
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization[7:]
    decoded = FirebaseService().verify_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    return decoded.get("uid")


@router.post("/tts")
async def text_to_speech(
    request: Request,
    user_id: str = Depends(get_current_user),
) -> dict:
    data = await request.json()
    text = data.get("text")
    voice_id = data.get("voice_id")
    speed = data.get("speed", 1.0)
    
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    
    return await voice_service.generate_tts(
        text=text,
        voice_id=voice_id,
        speed=speed,
    )


@router.post("/tts/with-presence")
async def tts_with_presence(
    text: str,
    voice_id: str,
    presence: str = "auto",
    user_id: str = Depends(get_current_user),
) -> dict:
    return await voice_service.generate_tts(
        text=text,
        voice_id=voice_id,
    )


@router.get("/health")
async def voice_health() -> dict:
    return await voice_service.health_check()


@router.post("/generate_token")
async def generate_voice_token(
    request: Request,
    user_id: str = Depends(get_current_user),
) -> dict:
    data = await request.json()
    character_id = data.get("character_id")
    session_id = data.get("session_id")
    
    token_data = await voice_service.generate_voice_token(
        session_id=session_id or f"session_{user_id}",
        user_id=user_id,
        character_id=character_id,
    )
    
    room_name = token_data.get("room_name") or token_data.get("room")
    
    if room_name:
        await voice_call_service.start_call(
            room_name=room_name,
            user_id=user_id,
            character_id=character_id,
            session_id=session_id,
        )
    
    return token_data


@router.post("/check-credits")
async def check_voice_call_credits(
    user_id: str = Depends(get_current_user),
) -> dict:
    return await voice_call_service.check_credits_for_call(user_id)


@router.post("/webhook/livekit")
async def livekit_webhook(
    request: Request,
) -> BaseResponse:
    body = await request.body()

    livekit_api_key = await get_config_value("LIVEKIT_API_KEY", settings.livekit_api_key)
    livekit_api_secret = await get_config_value("LIVEKIT_API_SECRET", settings.livekit_api_secret)
    
    if livekit_api_key and livekit_api_secret:
        try:
            from livekit import api as livekit_api
            
            webhook_receiver = livekit_api.WebhookReceiver(livekit_api_key, livekit_api_secret)
            event = webhook_receiver.receive(body.decode(), request.headers.get("Authorization", ""))
            
            logger.info(f"LiveKit webhook event: {event}")
            
            if event.room:
                room = event.room
                room_name = room.name
                
                if event.event == "room_finished":
                    call_result = await voice_call_service.end_call(room_name)
                    if call_result:
                        logger.info(
                            f"Voice call ended via webhook: room={room_name}, "
                            f"duration={call_result.get('duration_seconds', 0):.1f}s, "
                            f"credits={call_result.get('credits_charged', 0)}"
                        )
                
                elif event.event == "participant_joined":
                    logger.info(f"Participant joined room: {room_name}")
                
                elif event.event == "participant_left":
                    logger.info(f"Participant left room: {room_name}")
        
        except ImportError:
            logger.warning("livekit-server-sdk not installed, skipping webhook verification")
            try:
                event_data = json.loads(body)
                logger.info(f"LiveKit webhook (unverified): {event_data}")
                
                if event_data.get("event") == "room_finished":
                    room_name = event_data.get("room", {}).get("name")
                    if room_name:
                        await voice_call_service.end_call(room_name)
            except json.JSONDecodeError:
                logger.error("Failed to parse webhook body as JSON")
        
        except Exception as e:
            logger.error(f"Error processing LiveKit webhook: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    else:
        try:
            event_data = json.loads(body)
            logger.info(f"LiveKit webhook (no verification): {event_data}")
            
            if event_data.get("event") == "room_finished":
                room_name = event_data.get("room", {}).get("name")
                if room_name:
                    await voice_call_service.end_call(room_name)
        except json.JSONDecodeError:
            logger.error("Failed to parse webhook body as JSON")
    
    return BaseResponse(success=True, message="Webhook received")


@router.get("/call-status/{room_name}")
async def get_call_status(
    room_name: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    call_data = await voice_call_service.get_call(room_name)
    if not call_data:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if call_data.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    duration = await voice_call_service.get_active_call_duration(room_name)
    
    return {
        "room_name": room_name,
        "status": call_data.get("status"),
        "duration_seconds": duration,
        "start_time": call_data.get("start_time"),
    }
