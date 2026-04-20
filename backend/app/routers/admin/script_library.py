"""
Admin: Script Library Management
Handles CRUD, mature review, bulk ops, and stats for script_library.
"""
import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query

from app.core.database import db
from app.models.script_library import ScriptLibraryUpdate, ScriptLibraryStatus
from app.services.script_library_service import script_library_service

router = APIRouter(prefix="/api/admin/script-library", tags=["admin-script-library"])
logger = logging.getLogger(__name__)


# ── Stats ────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats() -> dict[str, Any]:
    total = await db.execute("SELECT COUNT(*) as c FROM script_library", fetch=True)
    by_rating = await db.execute(
        "SELECT age_rating, COUNT(*) as c FROM script_library GROUP BY age_rating",
        fetch_all=True,
    )
    by_status = await db.execute(
        "SELECT status, COUNT(*) as c FROM script_library GROUP BY status",
        fetch_all=True,
    )
    mature_by_relation = await db.execute(
        """SELECT relation_types, COUNT(*) as c FROM script_library
           WHERE age_rating = 'mature' GROUP BY relation_types ORDER BY c DESC LIMIT 20""",
        fetch_all=True,
    )
    return {
        "total": total["c"] if total else 0,
        "by_age_rating": {r["age_rating"]: r["c"] for r in (by_rating or [])},
        "by_status": {r["status"]: r["c"] for r in (by_status or [])},
        "mature_top_relations": [
            {"relation_types": r["relation_types"], "count": r["c"]}
            for r in (mature_by_relation or [])
        ],
    }


# ── List (admin, all ratings) ─────────────────────────────────────────────────

@router.get("")
async def list_scripts(
    age_rating: Optional[str] = Query(None, description="Filter: all | mature"),
    status: Optional[str] = Query(None, description="Filter: published | draft | archived"),
    relation_types: Optional[str] = Query(None, description="Comma-separated"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    filters: dict[str, Any] = {}
    if age_rating:
        filters["age_rating"] = age_rating
    if status:
        filters["status"] = status
    if relation_types:
        filters["relation_types"] = [t.strip() for t in relation_types.split(",")]
    if search:
        filters["search"] = search

    result = await script_library_service.list_scripts(
        page=page,
        page_size=page_size,
        **filters,
    )
    return {
        "items": [s.model_dump() for s in result.items],
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
        "total_pages": (result.total + page_size - 1) // page_size if result.total else 0,
    }


# ── Single script ─────────────────────────────────────────────────────────────

@router.get("/{script_id}")
async def get_script(script_id: str) -> dict[str, Any]:
    script = await script_library_service.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script.model_dump()


@router.put("/{script_id}")
async def update_script(script_id: str, data: ScriptLibraryUpdate) -> dict[str, Any]:
    script = await script_library_service.update_script(script_id, data)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return script.model_dump()


@router.delete("/{script_id}")
async def delete_script(script_id: str) -> dict[str, Any]:
    success = await script_library_service.delete_script(script_id)
    if not success:
        raise HTTPException(status_code=404, detail="Script not found")
    return {"success": True, "message": f"Script '{script_id}' deleted"}


# ── Mature content review ────────────────────────────────────────────────────

@router.get("/mature/pending")
async def list_mature_pending(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    """Mature 劇本草稿審核列表（status=draft）"""
    result = await script_library_service.list_scripts(
        age_rating="mature",
        status="draft",
        page=page,
        page_size=page_size,
    )
    return {
        "items": [s.model_dump() for s in result.items],
        "total": result.total,
        "page": result.page,
        "page_size": result.page_size,
    }


@router.post("/{script_id}/publish")
async def publish_script(script_id: str) -> dict[str, Any]:
    script = await script_library_service.update_script(
        script_id,
        ScriptLibraryUpdate(status=ScriptLibraryStatus.PUBLISHED),
    )
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return {"success": True, "script_id": script_id, "status": "published"}


@router.post("/{script_id}/archive")
async def archive_script(script_id: str) -> dict[str, Any]:
    script = await script_library_service.update_script(
        script_id,
        ScriptLibraryUpdate(status=ScriptLibraryStatus.ARCHIVED),
    )
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return {"success": True, "script_id": script_id, "status": "archived"}


@router.post("/{script_id}/downgrade")
async def downgrade_to_all(script_id: str) -> dict[str, Any]:
    """將 Mature 劇本降級為 all（適合在不確定是否合規時使用）"""
    script = await script_library_service.update_script(
        script_id,
        ScriptLibraryUpdate(age_rating="all"),
    )
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return {"success": True, "script_id": script_id, "age_rating": "all"}


# ── Bulk operations ───────────────────────────────────────────────────────────

@router.post("/bulk/publish")
async def bulk_publish(body: dict[str, Any]) -> dict[str, Any]:
    """批量發布劇本。Body: {"ids": ["id1", "id2", ...]}"""
    ids: list[str] = body.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="No script IDs provided")
    if len(ids) > 500:
        raise HTTPException(status_code=400, detail="Max 500 IDs per batch")

    placeholders = ",".join("?" * len(ids))
    await db.execute(
        f"UPDATE script_library SET status = 'published' WHERE id IN ({placeholders})",
        tuple(ids),
    )
    return {"success": True, "updated": len(ids)}


@router.post("/bulk/archive")
async def bulk_archive(body: dict[str, Any]) -> dict[str, Any]:
    """批量封存劇本。Body: {"ids": [...]}"""
    ids: list[str] = body.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="No script IDs provided")
    if len(ids) > 500:
        raise HTTPException(status_code=400, detail="Max 500 IDs per batch")

    placeholders = ",".join("?" * len(ids))
    await db.execute(
        f"UPDATE script_library SET status = 'archived' WHERE id IN ({placeholders})",
        tuple(ids),
    )
    return {"success": True, "updated": len(ids)}


@router.post("/bulk/delete")
async def bulk_delete(body: dict[str, Any]) -> dict[str, Any]:
    """批量刪除劇本。Body: {"ids": [...]}"""
    ids: list[str] = body.get("ids", [])
    if not ids:
        raise HTTPException(status_code=400, detail="No script IDs provided")
    if len(ids) > 200:
        raise HTTPException(status_code=400, detail="Max 200 IDs per batch")

    placeholders = ",".join("?" * len(ids))
    await db.execute(
        f"DELETE FROM script_library WHERE id IN ({placeholders})",
        tuple(ids),
    )
    return {"success": True, "deleted": len(ids)}


@router.post("/bulk/set-age-rating")
async def bulk_set_age_rating(body: dict[str, Any]) -> dict[str, Any]:
    """批量設定 age_rating。Body: {"ids": [...], "age_rating": "mature|all"}"""
    ids: list[str] = body.get("ids", [])
    age_rating: str = body.get("age_rating", "")
    if not ids:
        raise HTTPException(status_code=400, detail="No script IDs provided")
    if age_rating not in {"all", "mature"}:
        raise HTTPException(status_code=400, detail="age_rating must be: all | mature")
    if len(ids) > 500:
        raise HTTPException(status_code=400, detail="Max 500 IDs per batch")

    placeholders = ",".join("?" * len(ids))
    await db.execute(
        f"UPDATE script_library SET age_rating = ? WHERE id IN ({placeholders})",
        (age_rating, *ids),
    )
    return {"success": True, "updated": len(ids), "age_rating": age_rating}


# ── Mature pair helper ───────────────────────────────────────────────────────

@router.get("/{script_id}/mature-pair")
async def get_mature_pair(script_id: str) -> dict[str, Any]:
    """查詢某劇本的 Mature 克隆，或 Mature 劇本對應的原版。"""
    if script_id.endswith("_mature"):
        original_id = script_id[:-7]
        original = await script_library_service.get_script(original_id)
        mature = await script_library_service.get_script(script_id)
        return {
            "original": original.model_dump() if original else None,
            "mature": mature.model_dump() if mature else None,
        }
    else:
        mature_id = f"{script_id}_mature"
        original = await script_library_service.get_script(script_id)
        mature = await script_library_service.get_script(mature_id)
        return {
            "original": original.model_dump() if original else None,
            "mature": mature.model_dump() if mature else None,
        }
