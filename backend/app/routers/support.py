from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Any, Optional

from app.models import BaseResponse
from app.core.dependencies import get_current_user_required, get_admin_user
from app.services.support_service import support_service

router = APIRouter(prefix="/api/billing/support", tags=["support"])


@router.post("")
async def create_support_ticket(
    request: Request,
    data: dict[str, Any],
    user=Depends(get_current_user_required),
) -> dict[str, Any]:
    try:
        ticket = await support_service.create_ticket(
            user_id=user.id,
            user_email=user.email,
            issue_type=data.get("issue_type") or data.get("category"),
            message=data.get("description") or data.get("message") or "",
            order_id=data.get("order_id"),
            subject=data.get("subject"),
            category=data.get("category"),
            priority=data.get("priority"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "success": True,
        "id": ticket["id"],
        "status": ticket["status"],
        "message": "Support ticket created",
    }


@router.get("")
async def list_support_tickets(
    request: Request,
    user=Depends(get_current_user_required),
) -> list[dict[str, Any]]:
    tickets = await support_service.list_user_tickets(user_id=user.id)
    return tickets


@router.post("/feedback", response_model=BaseResponse)
async def submit_feedback(
    request: Request,
    data: dict[str, Any],
    user=Depends(get_current_user_required),
) -> BaseResponse:
    rating = data.get("rating")
    feedback_type = data.get("feedback_type")
    comment = data.get("comment") or data.get("content")
    try:
        await support_service.submit_feedback(
            user_id=user.id,
            user_email=user.email,
            rating=int(rating) if rating is not None else None,
            comment=comment,
            feedback_type=feedback_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return BaseResponse(success=True, message="Feedback submitted")


admin_support_router = APIRouter(prefix="/admin/support-tickets", tags=["admin-support"])


@admin_support_router.get("")
async def list_admin_tickets(
    request: Request,
    status: Optional[str] = None,
    limit: int = 100,
    admin=Depends(get_admin_user),
) -> list[dict[str, Any]]:
    tickets = await support_service.list_admin_tickets(status=status, limit=limit)
    return tickets


@admin_support_router.post("/{ticket_id}/resolve", response_model=BaseResponse)
async def resolve_ticket(
    request: Request,
    ticket_id: str,
    data: dict[str, Any],
    admin=Depends(get_admin_user),
) -> BaseResponse:
    resolution = data.get("resolution") or data.get("comment")
    credits_granted = data.get("credits_granted")
    status = data.get("status") or "resolved"
    try:
        await support_service.resolve_ticket(
            ticket_id=ticket_id,
            admin_email=admin.email,
            resolution=resolution,
            credits_granted=float(credits_granted) if credits_granted is not None else None,
            status=status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return BaseResponse(success=True, message="Ticket resolved")
