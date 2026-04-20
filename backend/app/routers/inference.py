from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
import logging

from ..services.inference_router import inference_router
from ..services.intent_router import intent_router
from ..services.local_inference import local_inference_service
from ..services.streaming_tts import streaming_tts_service
from ..services.embedding_service import embedding_service
from ..services.vector_store import memory_vector_store, global_memory_vector_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inference", tags=["inference"])


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    from ..services import FirebaseService
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization[7:]
    decoded = FirebaseService().verify_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    return decoded.get("uid")


@router.get("/health")
async def inference_health() -> dict:
    return await inference_router.health_check()


@router.get("/route")
async def get_route_info(text: str) -> dict:
    return inference_router.get_route_info(text)


@router.post("/generate")
async def generate(
    messages: list[dict],
    user_message: Optional[str] = None,
    force_cloud: bool = False,
    user_id: str = Depends(get_current_user),
) -> dict:
    return await inference_router.generate(
        messages=messages,
        user_message=user_message,
        force_cloud=force_cloud,
    )


@router.get("/intent/classify")
async def classify_intent(text: str) -> dict:
    use_local, intent, confidence = intent_router.should_use_local_model(text)
    return {
        "intent": intent.value,
        "confidence": confidence,
        "use_local_model": use_local,
    }


@router.get("/local/health")
async def local_model_health() -> dict:
    return await local_inference_service.health_check()


@router.get("/tts/health")
async def tts_health() -> dict:
    return await streaming_tts_service.health_check()


@router.get("/embedding/health")
async def embedding_health() -> dict:
    return await embedding_service.health_check()


@router.get("/vector/health")
async def vector_health() -> dict:
    memory_health = await memory_vector_store.health_check()
    global_health = await global_memory_vector_store.health_check()
    
    return {
        "status": "healthy" if memory_health["status"] == "healthy" else "degraded",
        "memory_vector_store": memory_health,
        "global_memory_vector_store": global_health,
    }


@router.get("/system/health")
async def system_health() -> dict:
    inference = await inference_router.health_check()
    embedding = await embedding_service.health_check()
    vector = await memory_vector_store.health_check()
    tts = await streaming_tts_service.health_check()
    
    all_healthy = all([
        inference["status"] == "healthy",
        embedding["status"] in ("healthy", "fallback"),
        vector["status"] in ("healthy", "unavailable"),
        tts["status"] == "healthy",
    ])
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "services": {
            "inference": inference,
            "embedding": embedding,
            "vector_store": vector,
            "streaming_tts": tts,
        },
    }
