from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user_required
from app.services.reward_service import reward_service

router = APIRouter(prefix="/api/rewards", tags=["rewards"])


class ShareRewardClaimRequest(BaseModel):
    share_key: str = Field(..., min_length=1, max_length=128)
    channel: Optional[str] = Field(default="unknown", max_length=32)
    metadata: Optional[dict[str, Any]] = None


@router.post("/share/claim")
async def claim_share_reward(
    request: Request,
    data: ShareRewardClaimRequest,
    user=Depends(get_current_user_required),
) -> dict[str, Any]:
    try:
        return await reward_service.claim_share_reward(
            user_id=user.id,
            share_key=data.share_key,
            channel=data.channel,
            metadata=data.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to claim share reward: {exc}")
