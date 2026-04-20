from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any

from app.models import BaseResponse, SupportTicketCreate, SupportTicketFeedback

router = APIRouter(prefix="/api/billing/support", tags=["support"])


@router.post("", response_model=BaseResponse)
async def create_support_ticket(
    request: Request, 
    data: SupportTicketCreate
) -> BaseResponse:
    return BaseResponse(success=True, message="Support ticket created")


@router.get("")
async def list_support_tickets(request: Request) -> list[dict[str, Any]]:
    return [
        {
            "id": "ticket_001",
            "subject": "Billing Issue",
            "status": "open",
            "priority": "high",
            "created_at": datetime.now().isoformat(),
        }
    ]


@router.post("/feedback", response_model=BaseResponse)
async def submit_feedback(
    request: Request, 
    data: SupportTicketFeedback
) -> BaseResponse:
    return BaseResponse(success=True, message="Feedback submitted")


admin_support_router = APIRouter(prefix="/admin/support-tickets", tags=["admin-support"])


@admin_support_router.get("")
async def list_admin_tickets(request: Request) -> list[dict[str, Any]]:
    return [
        {
            "id": "ticket_001",
            "subject": "Support Request",
            "user_id": "user_001",
            "status": "open",
            "priority": "medium",
            "created_at": datetime.now().isoformat(),
        }
    ]


@admin_support_router.post("/{ticket_id}/resolve", response_model=BaseResponse)
async def resolve_ticket(request: Request, ticket_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Ticket resolved")
