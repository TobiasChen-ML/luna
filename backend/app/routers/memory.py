from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
import logging

from ..services.memory_service import MemoryService
from ..services.embedding_service import embedding_service
from ..services.vector_store import memory_vector_store, global_memory_vector_store
from ..models.schemas import BaseResponse
from ..models.memory import (
    MemoryCreate,
    GlobalMemoryCreate,
    GlobalMemoryPromoteRequest,
    MemoryForgetRequest,
    MemoryCorrectRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/context", tags=["memory"])

memory_service = MemoryService()


async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    from ..services import FirebaseService
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization")
    
    token = authorization[7:]
    decoded = FirebaseService().verify_token(token)
    if not decoded:
        raise HTTPException(status_code=401, detail="Invalid token")
    return decoded.get("uid")


@router.get("/{character_id}")
async def get_context(
    character_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    return await memory_service.get_context(character_id, user_id)


@router.get("/{character_id}/memory")
async def get_memory(
    character_id: str,
    query: Optional[str] = None,
    layer: Optional[str] = None,
    limit: int = 10,
    user_id: str = Depends(get_current_user),
) -> dict:
    if query:
        memories = await memory_service.query_memories(
            user_id=user_id,
            character_id=character_id,
            query=query,
            layer=layer,
            limit=limit,
        )
        return {"memories": memories, "query": query}
    
    context = await memory_service.get_context(character_id, user_id)
    return context


@router.post("/{character_id}/memory/forget")
async def forget_memory(
    character_id: str,
    request: MemoryForgetRequest,
    user_id: str = Depends(get_current_user),
) -> dict:
    return await memory_service.forget_memories(
        user_id=user_id,
        character_id=character_id,
        memory_ids=request.memory_ids,
    )


@router.post("/{character_id}/memory/correct")
async def correct_memory(
    character_id: str,
    request: MemoryCorrectRequest,
    user_id: str = Depends(get_current_user),
) -> dict:
    return await memory_service.correct_memory(
        user_id=user_id,
        character_id=character_id,
        memory_id=request.memory_id,
        new_content=request.new_content,
    )


@router.post("/{character_id}/memory")
async def add_memory(
    character_id: str,
    request: MemoryCreate,
    user_id: str = Depends(get_current_user),
) -> dict:
    return await memory_service.add_memory(
        user_id=user_id,
        character_id=character_id,
        content=request.content,
        layer=request.layer.value if hasattr(request.layer, 'value') else request.layer,
        importance=request.importance,
        metadata=request.metadata,
    )


@router.post("/index")
async def index_memory(
    user_id: str,
    character_id: str,
    content: str,
    metadata: Optional[dict] = None,
) -> dict:
    return await memory_service.index_memory(user_id, character_id, content, metadata)


@router.post("/query")
async def query_memory(
    user_id: str,
    character_id: str,
    query: str,
    layer: Optional[str] = None,
    limit: int = 10,
) -> dict:
    memories = await memory_service.query_memories(
        user_id=user_id,
        character_id=character_id,
        query=query,
        layer=layer,
        limit=limit,
    )
    return {"memories": memories, "query": query}


@router.post("/extract")
async def extract_memory(
    user_id: str,
    character_id: str,
    conversation: list[dict],
) -> dict:
    memories = await memory_service.extract_and_store(user_id, character_id, conversation)
    return {"extracted_count": len(memories), "memories": memories}


@router.delete("/index/{memory_id}")
async def delete_memory(
    memory_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    return await memory_service.forget_memories(user_id, "", [memory_id])


@router.get("/stats")
async def get_memory_stats(user_id: str = Depends(get_current_user)) -> dict:
    return await memory_service.get_memory_stats(user_id)


@router.get("/health")
async def memory_health() -> dict:
    return await memory_service.health_check()


@router.post("/decay/update")
async def update_decay() -> dict:
    updated = await memory_service.update_all_decayed_importance()
    return {"updated_count": updated}


@router.get("/global")
async def get_global_memories(user_id: str = Depends(get_current_user)) -> dict:
    memories = await memory_service._get_global_memories(user_id)
    return {"memories": memories}


@router.get("/global/suggestions")
async def get_global_memory_suggestions(user_id: str = Depends(get_current_user)) -> dict:
    suggestions = await memory_service.suggest_global_memories(user_id)
    return {"suggestions": suggestions}


@router.post("/global")
async def create_global_memory(
    request: GlobalMemoryCreate,
    user_id: str = Depends(get_current_user),
) -> dict:
    return await memory_service.create_global_memory(
        user_id=user_id,
        content=request.content,
        category=request.category.value if hasattr(request.category, 'value') else request.category,
        source_character_id=request.source_character_id,
        confidence=request.confidence,
    )


@router.post("/global/promote")
async def promote_to_global_memory(
    request: GlobalMemoryPromoteRequest,
    user_id: str = Depends(get_current_user),
) -> dict:
    return await memory_service.promote_to_global(
        user_id=user_id,
        memory_id=request.memory_id,
        category=request.category.value if hasattr(request.category, 'value') else request.category,
    )


@router.post("/global/{global_memory_id}/confirm")
async def confirm_global_memory(
    global_memory_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    return await memory_service.confirm_global_memory(user_id, global_memory_id)


@router.delete("/global/{global_memory_id}")
async def delete_global_memory(
    global_memory_id: str,
    user_id: str = Depends(get_current_user),
) -> dict:
    return await memory_service.delete_global_memory(user_id, global_memory_id)


@router.get("/vector/health")
async def vector_store_health() -> dict:
    embedding_health = await embedding_service.health_check()
    memory_vs_health = await memory_vector_store.health_check()
    global_vs_health = await global_memory_vector_store.health_check()
    
    return {
        "embedding": embedding_health,
        "memory_vector_store": memory_vs_health,
        "global_memory_vector_store": global_vs_health,
        "overall_status": "healthy" if embedding_health["status"] in ("healthy", "fallback") else "degraded",
    }


@router.post("/vector/rebuild")
async def rebuild_vector_store(
    user_id: str = Depends(get_current_user),
) -> dict:
    from ..migrations.migrate_memory_embeddings import rebuild_vector_store
    
    try:
        await rebuild_vector_store()
        return {"status": "success", "message": "Vector store rebuilt successfully"}
    except Exception as e:
        logger.error(f"Failed to rebuild vector store: {e}")
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")
