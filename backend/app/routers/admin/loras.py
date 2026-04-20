import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field
import aiosqlite
import logging

from app.core.dependencies import get_admin_user
from app.core.database import db

router = APIRouter(prefix="/api/admin/loras", tags=["admin-loras"])
logger = logging.getLogger(__name__)

AppliesTo = Literal["txt2img", "img2img", "video", "all"]


class LoRAPresetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    model_name: str = Field(..., min_length=1, max_length=255)
    strength: float = Field(default=0.8, ge=0.0, le=2.0)
    trigger_word: str = Field(default="", max_length=500)
    description: str = Field(default="", max_length=1000)
    applies_to: AppliesTo = "all"
    provider: str = Field(default="novita", max_length=50)
    is_active: bool = True


class LoRAPresetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    model_name: Optional[str] = Field(None, min_length=1, max_length=255)
    strength: Optional[float] = Field(None, ge=0.0, le=2.0)
    trigger_word: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=1000)
    applies_to: Optional[AppliesTo] = None
    provider: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


def _row_to_dict(row: Optional[aiosqlite.Row]) -> dict[str, Any]:
    return dict(row) if row else {}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.get("")
async def list_loras(
    applies_to: Optional[str] = None,
    active_only: bool = False,
    _admin=Depends(get_admin_user),
) -> dict[str, Any]:
    conditions = []
    params: list[Any] = []

    # When filtering by a specific scope, include rows scoped to 'all' as well.
    # Skip the filter entirely when applies_to is omitted or is 'all'.
    if applies_to and applies_to != "all":
        conditions.append("(applies_to = ? OR applies_to = 'all')")
        params.append(applies_to)
    if active_only:
        conditions.append("is_active = 1")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = await db.execute(
        f"SELECT * FROM lora_presets {where} ORDER BY created_at DESC",
        tuple(params),
        fetch_all=True,
    )
    return {"loras": [_row_to_dict(r) for r in (rows or [])]}


@router.post("")
async def create_lora(
    data: LoRAPresetCreate,
    _admin=Depends(get_admin_user),
) -> dict[str, Any]:
    lora_id = str(uuid.uuid4())
    now = _utcnow()
    await db.execute(
        """INSERT INTO lora_presets
           (id, name, model_name, strength, trigger_word, description, applies_to, provider, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            lora_id,
            data.name,
            data.model_name,
            data.strength,
            data.trigger_word,
            data.description,
            data.applies_to,
            data.provider,
            1 if data.is_active else 0,
            now,
            now,
        ),
    )
    row = await db.execute(
        "SELECT * FROM lora_presets WHERE id = ?", (lora_id,), fetch=True
    )
    return {"lora": _row_to_dict(row)}


@router.put("/{lora_id}")
async def update_lora(
    lora_id: str,
    data: LoRAPresetUpdate,
    _admin=Depends(get_admin_user),
) -> dict[str, Any]:
    row = await db.execute(
        "SELECT * FROM lora_presets WHERE id = ?", (lora_id,), fetch=True
    )
    if not row:
        raise HTTPException(status_code=404, detail="LoRA preset not found")

    updates = data.model_dump(exclude_none=True)
    if not updates:
        return {"lora": _row_to_dict(row)}

    if "is_active" in updates:
        updates["is_active"] = 1 if updates["is_active"] else 0

    updates["updated_at"] = _utcnow()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    params = list(updates.values()) + [lora_id]
    await db.execute(
        f"UPDATE lora_presets SET {set_clause} WHERE id = ?", tuple(params)
    )
    updated = await db.execute(
        "SELECT * FROM lora_presets WHERE id = ?", (lora_id,), fetch=True
    )
    return {"lora": _row_to_dict(updated)}


@router.delete("/{lora_id}")
async def delete_lora(
    lora_id: str,
    _admin=Depends(get_admin_user),
) -> dict[str, Any]:
    row = await db.execute(
        "SELECT id FROM lora_presets WHERE id = ?", (lora_id,), fetch=True
    )
    if not row:
        raise HTTPException(status_code=404, detail="LoRA preset not found")
    await db.execute("DELETE FROM lora_presets WHERE id = ?", (lora_id,))
    return {"success": True}
