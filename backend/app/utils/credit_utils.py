import logging
from functools import wraps
from typing import Optional, Callable
from fastapi import HTTPException

from ..services.credit_service import credit_service, InsufficientCreditsError
from ..services.pricing_service import pricing_service
from ..models.user import User

logger = logging.getLogger(__name__)


async def check_and_deduct_credits(
    user: User,
    usage_type: str,
    character_id: Optional[str] = None,
    session_id: Optional[str] = None,
    skip_for_premium: bool = True,
) -> bool:
    """
    Check and deduct credits for a usage.
    
    Args:
        user: The user object
        usage_type: message, voice, image, video, voice_call
        character_id: Optional character ID
        session_id: Optional session ID
        skip_for_premium: If True, skip deduction for premium users for message usage
    
    Returns:
        True if credits were deducted (or skipped for premium)
    
    Raises:
        HTTPException 402 if insufficient credits
    """
    config = await credit_service.get_config()
    
    cost_map = {
        "message": config.message_cost,
        "voice": config.voice_cost,
        "image": config.image_cost,
        "video": config.video_cost,
        "voice_call": config.voice_call_per_minute,
    }
    
    amount = cost_map.get(usage_type)
    if amount is None:
        logger.warning(f"Unknown usage_type: {usage_type}")
        return True
    
    if skip_for_premium and usage_type == "message":
        if user.subscription_tier and user.subscription_tier != "free":
            logger.debug(f"Premium user {user.id}, skipping message deduction")
            return True
    
    balance = await credit_service.get_balance(user.id)
    if balance["total"] < amount:
        logger.warning(f"User {user.id} has insufficient credits: {balance['total']} < {amount}")
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. You have {balance['total']} credits, need {amount} for {usage_type}."
        )
    
    try:
        await credit_service.deduct_credits(
            user_id=user.id,
            amount=amount,
            usage_type=usage_type,
            character_id=character_id,
            session_id=session_id,
            description=f"Used {amount} credits for {usage_type}",
        )
        logger.info(f"Deducted {amount} credits from user {user.id} for {usage_type}")
        return True
    except InsufficientCreditsError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to deduct credits: {e}")
        raise HTTPException(status_code=500, detail="Failed to process credits")


async def get_user_balance_safe(user_id: int) -> dict:
    """Get user balance, returns default values if user not found."""
    try:
        return await credit_service.get_balance(user_id)
    except Exception as e:
        logger.error(f"Failed to get balance for user {user_id}: {e}")
        return {
            "total": 0.0,
            "purchased": 0.0,
            "monthly": 0.0,
            "subscription_tier": "free",
        }


async def grant_signup_bonus_safe(user_id: int) -> bool:
    """Grant signup bonus, returns False if already granted or error."""
    try:
        return await credit_service.grant_signup_bonus(user_id)
    except Exception as e:
        logger.error(f"Failed to grant signup bonus for user {user_id}: {e}")
        return False