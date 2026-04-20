import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any, Optional

from app.models import BaseResponse
from app.models.script import (
    ScriptCreate,
    ScriptUpdate,
    ScriptNodeCreate,
    ScriptNodeUpdate,
    ScriptStatus,
    ScriptReviewCreate,
)
from app.services.script_service import script_service

router = APIRouter(prefix="/api/admin/scripts", tags=["admin-scripts"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_scripts(
    request: Request,
    character_id: Optional[str] = None,
    status: Optional[str] = None,
) -> list[dict[str, Any]]:
    scripts = await script_service.list_scripts(
        character_id=character_id,
        status=status,
    )
    return scripts


@router.post("")
async def create_script(request: Request, data: ScriptCreate) -> dict[str, Any]:
    script = await script_service.create_script(data)
    return script


@router.get("/{script_id}")
async def get_script(request: Request, script_id: str) -> dict[str, Any]:
    script = await script_service.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail=f"Script '{script_id}' not found")
    return script


@router.put("/{script_id}")
async def update_script(
    request: Request,
    script_id: str,
    data: ScriptUpdate,
) -> dict[str, Any]:
    script = await script_service.update_script(script_id, data)
    if not script:
        raise HTTPException(status_code=404, detail=f"Script '{script_id}' not found")
    return script


@router.delete("/{script_id}", response_model=BaseResponse)
async def delete_script(request: Request, script_id: str) -> BaseResponse:
    success = await script_service.delete_script(script_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Script '{script_id}' not found")
    return BaseResponse(success=True, message=f"Script '{script_id}' deleted")


@router.post("/{script_id}/publish", response_model=BaseResponse)
async def publish_script(request: Request, script_id: str) -> BaseResponse:
    script = await script_service.update_script(
        script_id,
        ScriptUpdate(status=ScriptStatus.PUBLISHED),
    )
    if not script:
        raise HTTPException(status_code=404, detail=f"Script '{script_id}' not found")
    return BaseResponse(success=True, message=f"Script '{script_id}' published")


@router.get("/{script_id}/nodes")
async def list_nodes(request: Request, script_id: str) -> list[dict[str, Any]]:
    nodes = await script_service.list_nodes(script_id)
    return nodes


@router.post("/{script_id}/nodes")
async def create_node(
    request: Request,
    script_id: str,
    data: ScriptNodeCreate,
) -> dict[str, Any]:
    data.script_id = script_id
    node = await script_service.create_node(data)
    return node


@router.get("/{script_id}/nodes/{node_id}")
async def get_node(
    request: Request,
    script_id: str,
    node_id: str,
) -> dict[str, Any]:
    node = await script_service.get_node(node_id)
    if not node or node.get("script_id") != script_id:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return node


@router.put("/{script_id}/nodes/{node_id}")
async def update_node(
    request: Request,
    script_id: str,
    node_id: str,
    data: ScriptNodeUpdate,
) -> dict[str, Any]:
    node = await script_service.update_node(node_id, data)
    if not node:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return node


@router.delete("/{script_id}/nodes/{node_id}", response_model=BaseResponse)
async def delete_node(
    request: Request,
    script_id: str,
    node_id: str,
) -> BaseResponse:
    success = await script_service.delete_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
    return BaseResponse(success=True, message=f"Node '{node_id}' deleted")


@router.post("/{script_id}/validate")
async def validate_script(request: Request, script_id: str) -> dict[str, Any]:
    script = await script_service.get_script(script_id)
    if not script:
        raise HTTPException(status_code=404, detail=f"Script '{script_id}' not found")
    
    nodes = await script_service.list_nodes(script_id)
    
    errors = []
    
    if not script.get("start_node_id"):
        errors.append({"field": "start_node_id", "message": "Start node is not defined"})
    
    if not nodes:
        errors.append({"field": "nodes", "message": "Script has no nodes"})
    
    node_ids = {n["id"] for n in nodes}
    for node in nodes:
        choices = node.get("choices") or []
        for choice in choices:
            next_id = choice.get("next_node_id")
            if next_id and next_id not in node_ids:
                errors.append({
                    "field": f"nodes.{node['id']}.choices",
                    "message": f"Invalid next_node_id: {next_id}"
                })
    
    return {
        "script_id": script_id,
        "valid": len(errors) == 0,
        "errors": errors,
        "node_count": len(nodes),
    }


@router.get("/pending")
async def list_pending_scripts(
    request: Request,
    page: int = 1,
    page_size: int = 20
) -> dict[str, Any]:
    scripts, total = await script_service.list_pending_reviews(page, page_size)
    return {
        "scripts": scripts,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
    }


@router.post("/{script_id}/submit-review", response_model=BaseResponse)
async def submit_script_for_review(
    request: Request,
    script_id: str,
    data: Optional[dict[str, Any]] = None
) -> BaseResponse:
    reviewer_id = getattr(request.state, "user_id", "admin")
    comment = data.get("comment") if data else None
    
    result = await script_service.submit_for_review(script_id, reviewer_id, comment)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot submit script for review")
    
    return BaseResponse(success=True, message="Script submitted for review")


@router.post("/{script_id}/approve", response_model=BaseResponse)
async def approve_script(
    request: Request,
    script_id: str,
    data: Optional[dict[str, Any]] = None
) -> BaseResponse:
    reviewer_id = getattr(request.state, "user_id", "admin")
    comment = data.get("comment") if data else None
    
    result = await script_service.approve_script(script_id, reviewer_id, comment)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot approve script")
    
    return BaseResponse(success=True, message="Script approved and published")


@router.post("/{script_id}/reject", response_model=BaseResponse)
async def reject_script(
    request: Request,
    script_id: str,
    data: Optional[dict[str, Any]] = None
) -> BaseResponse:
    reviewer_id = getattr(request.state, "user_id", "admin")
    comment = data.get("comment") if data else None
    
    result = await script_service.reject_script(script_id, reviewer_id, comment)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot reject script")
    
    return BaseResponse(success=True, message="Script rejected")


@router.get("/{script_id}/reviews")
async def get_script_reviews(
    request: Request,
    script_id: str
) -> list[dict[str, Any]]:
    reviews = await script_service.list_reviews(script_id)
    return reviews
