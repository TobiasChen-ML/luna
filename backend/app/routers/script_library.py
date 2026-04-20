"""
Script Library API Router
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.dependencies import get_optional_user
from app.models.script_library import (
    ScriptLibrary,
    ScriptLibraryCreate,
    ScriptLibraryUpdate,
    ScriptLibraryListResponse,
    ScriptTagsByCategory,
    ScriptTag,
)
from app.services.script_library_service import script_library_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/script-library", tags=["script-library"])

_ADULT_RATINGS = {"mature"}


def _resolve_age_rating_filter(
    age_rating: Optional[str],
    is_age_verified: bool,
) -> Optional[str]:
    """Return the effective age_rating filter based on verification status."""
    if age_rating in _ADULT_RATINGS and not is_age_verified:
        raise HTTPException(status_code=403, detail="Age verification required for mature content")
    if age_rating:
        return age_rating
    # Unverified users cannot see mature content without explicit opt-in
    return None if is_age_verified else "exclude_mature"


@router.get("", response_model=ScriptLibraryListResponse)
async def list_scripts(
    emotion_tones: Optional[str] = Query(None, description="Comma-separated emotion tone IDs"),
    relation_types: Optional[str] = Query(None, description="Comma-separated relation type IDs"),
    contrast_types: Optional[str] = Query(None, description="Comma-separated contrast type IDs"),
    era: Optional[str] = Query(None),
    gender_target: Optional[str] = Query(None),
    character_gender: Optional[str] = Query(None),
    profession: Optional[str] = Query(None),
    age_rating: Optional[str] = Query(None),
    length: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query("published"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_optional_user),
):
    is_age_verified: bool = False
    if current_user:
        import json as _json
        raw_meta = getattr(current_user, "user_metadata", None)
        if raw_meta:
            try:
                is_age_verified = bool(_json.loads(raw_meta).get("age_verified", False))
            except Exception:
                pass

    effective_rating = _resolve_age_rating_filter(age_rating, is_age_verified)

    filters = {}
    if emotion_tones:
        filters["emotion_tones"] = [t.strip() for t in emotion_tones.split(",")]
    if relation_types:
        filters["relation_types"] = [t.strip() for t in relation_types.split(",")]
    if contrast_types:
        filters["contrast_types"] = [t.strip() for t in contrast_types.split(",")]
    if era:
        filters["era"] = era
    if gender_target:
        filters["gender_target"] = gender_target
    if character_gender:
        filters["character_gender"] = character_gender
    if profession:
        filters["profession"] = profession
    if effective_rating:
        filters["age_rating"] = effective_rating
    if length:
        filters["length"] = length
    if search:
        filters["search"] = search
    if status:
        filters["status"] = status

    return await script_library_service.list_scripts(
        page=page,
        page_size=page_size,
        **filters
    )


@router.get("/random", response_model=List[ScriptLibrary])
async def get_random_scripts(
    count: int = Query(5, ge=1, le=20),
    status: str = Query("published"),
):
    return await script_library_service.get_random_scripts(count=count, status=status)


@router.get("/tags", response_model=ScriptTagsByCategory)
async def get_all_tags():
    return await script_library_service.get_all_tags()


@router.get("/tags/{category}", response_model=List[ScriptTag])
async def get_tags_by_category(category: str):
    return await script_library_service.get_tags_by_category(category)


@router.get("/{script_id}", response_model=ScriptLibrary)
async def get_script(script_id: str):
    script = await script_library_service.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    await script_library_service.increment_popularity(script_id)
    return script


@router.post("", response_model=ScriptLibrary)
async def create_script(data: ScriptLibraryCreate):
    return await script_library_service.create_script(data)


@router.put("/{script_id}", response_model=ScriptLibrary)
async def update_script(script_id: str, data: ScriptLibraryUpdate):
    script = await script_library_service.update_script(script_id, data)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script


@router.delete("/{script_id}")
async def delete_script(script_id: str):
    success = await script_library_service.delete_script(script_id)
    if not success:
        raise HTTPException(status_code=404, detail="Script not found")
    return {"success": True, "message": "Script deleted"}
