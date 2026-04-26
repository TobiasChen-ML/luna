import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.database import db
from app.core.dependencies import get_admin_user
from app.services.storage_service import storage_service


public_router = APIRouter(prefix="/api/images/openpose-presets", tags=["openpose-presets"])
admin_router = APIRouter(prefix="/api/admin/openpose-presets", tags=["admin-openpose-presets"])


class OpenPosePresetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    image_url: str = Field(..., min_length=1, max_length=1000)
    is_active: bool = True


class OpenPosePresetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    image_url: Optional[str] = Field(None, min_length=1, max_length=1000)
    is_active: Optional[bool] = None


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: Optional[dict[str, Any]]) -> dict[str, Any]:
    return dict(row) if row else {}


@public_router.get("")
async def list_public_openpose_presets() -> dict[str, Any]:
    rows = await db.execute(
        """SELECT id, name, image_url, is_active, created_at, updated_at
           FROM openpose_presets
           WHERE is_active = 1
           ORDER BY created_at DESC""",
        fetch_all=True,
    )
    return {"poses": [_row_to_dict(row) for row in (rows or [])]}


@admin_router.get("")
async def list_openpose_presets(
    active_only: bool = False,
    _admin=Depends(get_admin_user),
) -> dict[str, Any]:
    where = "WHERE is_active = 1" if active_only else ""
    rows = await db.execute(
        f"""SELECT id, name, image_url, is_active, created_at, updated_at
            FROM openpose_presets
            {where}
            ORDER BY created_at DESC""",
        fetch_all=True,
    )
    return {"poses": [_row_to_dict(row) for row in (rows or [])]}


@admin_router.post("")
async def create_openpose_preset(
    data: OpenPosePresetCreate,
    _admin=Depends(get_admin_user),
) -> dict[str, Any]:
    preset_id = str(uuid.uuid4())
    now = _utcnow()
    await db.execute(
        """INSERT INTO openpose_presets
           (id, name, image_url, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (preset_id, data.name, data.image_url, 1 if data.is_active else 0, now, now),
    )
    row = await db.execute("SELECT * FROM openpose_presets WHERE id = ?", (preset_id,), fetch=True)
    return {"pose": _row_to_dict(row)}


@admin_router.post("/upload")
async def upload_openpose_image(
    file: UploadFile = File(...),
    _admin=Depends(get_admin_user),
) -> dict[str, Any]:
    content_type = file.content_type or "application/octet-stream"
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    image_url = await storage_service.upload_bytes(
        content=content,
        folder="openpose",
        filename=file.filename,
        content_type=content_type,
    )
    return {"image_url": image_url}


@admin_router.put("/{pose_id}")
async def update_openpose_preset(
    pose_id: str,
    data: OpenPosePresetUpdate,
    _admin=Depends(get_admin_user),
) -> dict[str, Any]:
    row = await db.execute("SELECT * FROM openpose_presets WHERE id = ?", (pose_id,), fetch=True)
    if not row:
        raise HTTPException(status_code=404, detail="OpenPose preset not found")

    updates = data.model_dump(exclude_none=True)
    if not updates:
        return {"pose": _row_to_dict(row)}
    if "is_active" in updates:
        updates["is_active"] = 1 if updates["is_active"] else 0
    updates["updated_at"] = _utcnow()

    set_clause = ", ".join(f"{key} = ?" for key in updates)
    await db.execute(
        f"UPDATE openpose_presets SET {set_clause} WHERE id = ?",
        tuple(updates.values()) + (pose_id,),
    )
    updated = await db.execute("SELECT * FROM openpose_presets WHERE id = ?", (pose_id,), fetch=True)
    return {"pose": _row_to_dict(updated)}


@admin_router.delete("/{pose_id}")
async def delete_openpose_preset(
    pose_id: str,
    _admin=Depends(get_admin_user),
) -> dict[str, bool]:
    row = await db.execute("SELECT id FROM openpose_presets WHERE id = ?", (pose_id,), fetch=True)
    if not row:
        raise HTTPException(status_code=404, detail="OpenPose preset not found")
    await db.execute("DELETE FROM openpose_presets WHERE id = ?", (pose_id,))
    return {"success": True}
