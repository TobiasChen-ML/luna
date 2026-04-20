from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from typing import Any, Optional
import logging

from app.core.dependencies import get_admin_user
from app.models import BaseResponse
from app.services.audit_service import audit_service, AuditAction

router = APIRouter(prefix="/api/admin/audit", tags=["admin-audit"])
logger = logging.getLogger(__name__)


@router.get("/logs")
async def get_audit_logs(
    request: Request,
    admin = Depends(get_admin_user),
    admin_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    start_dt = None
    end_dt = None
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    logs, total = await audit_service.get_logs(
        admin_id=admin_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_dt,
        end_date=end_dt,
        limit=limit,
        offset=offset,
    )
    
    return {
        "logs": [log.to_dict() for log in logs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/logs/{log_id}")
async def get_audit_log_by_id(
    request: Request,
    log_id: int,
    admin = Depends(get_admin_user),
) -> dict[str, Any]:
    log = await audit_service.get_log_by_id(log_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return log.to_dict()


@router.get("/summary")
async def get_audit_summary(
    request: Request,
    admin = Depends(get_admin_user),
    admin_id: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
) -> dict[str, Any]:
    summary = await audit_service.get_admin_activity_summary(
        admin_id=admin_id,
        days=days,
    )
    
    return summary


@router.get("/actions")
async def get_available_actions(
    request: Request,
    admin = Depends(get_admin_user),
) -> list[str]:
    return [action.value for action in AuditAction]


@router.get("/resource-types")
async def get_resource_types(
    request: Request,
    admin = Depends(get_admin_user),
) -> list[str]:
    return [
        "character",
        "user",
        "credit_config",
        "credit_pack",
        "subscription_plan",
        "prompt_template",
        "script",
        "config",
        "api_key",
    ]