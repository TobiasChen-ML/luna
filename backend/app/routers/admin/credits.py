from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends
from typing import Any, Optional
from pydantic import BaseModel
import logging

from app.core.dependencies import get_admin_user, get_client_info
from app.models import BaseResponse
from app.services.credit_service import credit_service, InsufficientCreditsError
from app.services.pricing_service import pricing_service
from app.services.audit_service import audit_service, AuditAction
from app.schemas.credit import (
    CreditCostConfigResponse,
    CreditCostConfigUpdate,
    CreditPackCreate,
    CreditPackUpdate,
    SubscriptionPlanUpdate,
    AdminAdjustCreditsRequest,
)

router = APIRouter(prefix="/api/admin/credits", tags=["admin-credits"])
logger = logging.getLogger(__name__)


class BatchAdjustCreditsRequest(BaseModel):
    user_ids: list[str]
    amount: float
    description: str


class BatchAdjustResult(BaseModel):
    user_id: str
    success: bool
    error: Optional[str] = None
    new_balance: Optional[float] = None


@router.get("/config")
async def get_credit_config(
    request: Request,
    admin = Depends(get_admin_user)
) -> dict[str, Any]:
    config = await credit_service.get_config()
    return config


@router.put("/config")
async def update_credit_config(
    request: Request,
    data: CreditCostConfigUpdate,
    admin = Depends(get_admin_user)
) -> dict[str, Any]:
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    admin_email = getattr(admin, 'email', 'admin')
    admin_id = getattr(admin, 'id', 'admin')
    
    old_config = await credit_service.get_config()
    
    config = await credit_service.update_config(update_data, admin_email)
    
    client_info = get_client_info(request)
    await audit_service.log_action(
        admin_id=admin_id,
        admin_email=admin_email,
        action=AuditAction.CREDIT_CONFIG_UPDATE.value,
        resource_type="credit_config",
        resource_id="default",
        old_value=old_config,
        new_value=update_data,
        ip_address=client_info.get("ip_address"),
        user_agent=client_info.get("user_agent"),
    )
    
    return {
        "success": True,
        "message": "Credit config updated",
        "config": config,
    }


@router.get("/plans")
async def get_subscription_plans(
    request: Request,
    admin = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    plans = await pricing_service.get_subscription_plans(active_only=False)
    return [p.to_dict() for p in plans]


@router.put("/plans/{period}")
async def update_subscription_plan(
    request: Request,
    period: str,
    data: SubscriptionPlanUpdate,
    admin = Depends(get_admin_user)
) -> dict[str, Any]:
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    admin_email = getattr(admin, 'email', 'admin')
    admin_id = getattr(admin, 'id', 'admin')
    
    try:
        plan = await pricing_service.update_subscription_plan(period, **update_data)
        
        client_info = get_client_info(request)
        await audit_service.log_action(
            admin_id=admin_id,
            admin_email=admin_email,
            action=AuditAction.SUBSCRIPTION_PLAN_UPDATE.value,
            resource_type="subscription_plan",
            resource_id=period,
            new_value=update_data,
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
        )
        
        return {
            "success": True,
            "message": f"Subscription plan {period} updated",
            "plan": plan,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Database error updating subscription plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/packs")
async def get_credit_packs(
    request: Request,
    admin = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    packs = await pricing_service.get_credit_packs(active_only=False)
    return [p.to_dict() for p in packs]


@router.post("/packs")
async def create_credit_pack(
    request: Request,
    data: CreditPackCreate,
    admin = Depends(get_admin_user)
) -> dict[str, Any]:
    admin_email = getattr(admin, 'email', 'admin')
    admin_id = getattr(admin, 'id', 'admin')
    
    try:
        pack = await pricing_service.create_credit_pack(
            pack_id=data.pack_id,
            name=data.name,
            credits=data.credits,
            price_cents=data.price_cents,
            bonus_credits=data.bonus_credits,
            is_popular=data.is_popular,
            display_order=data.display_order,
        )
        
        client_info = get_client_info(request)
        await audit_service.log_action(
            admin_id=admin_id,
            admin_email=admin_email,
            action=AuditAction.CREDIT_PACK_CREATE.value,
            resource_type="credit_pack",
            resource_id=data.pack_id,
            new_value=data.model_dump(),
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
        )
        
        return {
            "success": True,
            "message": f"Credit pack {data.pack_id} created",
            "pack": pack.to_dict(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/packs/{pack_id}")
async def update_credit_pack(
    request: Request,
    pack_id: str,
    data: CreditPackUpdate,
    admin = Depends(get_admin_user)
) -> dict[str, Any]:
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    admin_email = getattr(admin, 'email', 'admin')
    admin_id = getattr(admin, 'id', 'admin')
    
    try:
        old_pack = await pricing_service.get_credit_pack(pack_id)
        old_value = old_pack.to_dict() if hasattr(old_pack, 'to_dict') else (old_pack if isinstance(old_pack, dict) else None)
        
        pack = await pricing_service.update_credit_pack(pack_id, **update_data)
        
        client_info = get_client_info(request)
        await audit_service.log_action(
            admin_id=admin_id,
            admin_email=admin_email,
            action=AuditAction.CREDIT_PACK_UPDATE.value,
            resource_type="credit_pack",
            resource_id=pack_id,
            old_value=old_value,
            new_value=update_data,
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
        )
        
        return {
            "success": True,
            "message": f"Credit pack {pack_id} updated",
            "pack": pack,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Database error updating credit pack: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/packs/{pack_id}")
async def delete_credit_pack(
    request: Request,
    pack_id: str,
    admin = Depends(get_admin_user)
) -> BaseResponse:
    admin_email = getattr(admin, 'email', 'admin')
    admin_id = getattr(admin, 'id', 'admin')
    
    old_pack = await pricing_service.get_credit_pack(pack_id)
    
    deleted = await pricing_service.delete_credit_pack(pack_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Credit pack {pack_id} not found")
    
    client_info = get_client_info(request)
    await audit_service.log_action(
        admin_id=admin_id,
        admin_email=admin_email,
        action=AuditAction.CREDIT_PACK_DELETE.value,
        resource_type="credit_pack",
        resource_id=pack_id,
        old_value=old_pack.to_dict() if old_pack else None,
        ip_address=client_info.get("ip_address"),
        user_agent=client_info.get("user_agent"),
    )
    
    return BaseResponse(success=True, message=f"Credit pack {pack_id} deleted")


@router.get("/transactions")
async def list_transactions(
    request: Request,
    admin = Depends(get_admin_user),
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
) -> dict[str, Any]:
    transactions, total = await credit_service.get_all_transactions(
        limit=limit,
        offset=offset,
        user_id=user_id,
        transaction_type=transaction_type,
    )
    return {
        "transactions": [t.to_dict() for t in transactions],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/adjust")
async def adjust_user_credits(
    request: Request,
    data: AdminAdjustCreditsRequest,
    admin = Depends(get_admin_user)
) -> BaseResponse:
    admin_email = getattr(admin, 'email', 'admin')
    admin_id = getattr(admin, 'id', 'admin')
    
    old_balance = await credit_service.get_balance(data.user_id)
    
    try:
        await credit_service.admin_adjust_credits(
            user_id=data.user_id,
            amount=data.amount,
            description=data.description,
            admin_email=admin_email,
        )
        
        new_balance = await credit_service.get_balance(data.user_id)
        
        client_info = get_client_info(request)
        await audit_service.log_action(
            admin_id=admin_id,
            admin_email=admin_email,
            action=AuditAction.CREDIT_ADJUST.value,
            resource_type="user",
            resource_id=data.user_id,
            old_value={"balance": old_balance.get("total", 0)},
            new_value={
                "adjustment": data.amount,
                "new_balance": new_balance.get("total", 0),
                "description": data.description,
            },
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
        )
        
        return BaseResponse(
            success=True,
            message=f"Adjusted {data.amount} credits for user {data.user_id}"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientCreditsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch-adjust")
async def batch_adjust_user_credits(
    request: Request,
    data: BatchAdjustCreditsRequest,
    admin = Depends(get_admin_user)
) -> dict[str, Any]:
    admin_email = getattr(admin, 'email', 'admin')
    admin_id = getattr(admin, 'id', 'admin')
    
    if not data.user_ids:
        raise HTTPException(status_code=400, detail="No user IDs provided")
    
    if len(data.user_ids) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 users per batch")
    
    results: list[BatchAdjustResult] = []
    success_count = 0
    failure_count = 0
    
    for user_id in data.user_ids:
        try:
            old_balance = await credit_service.get_balance(user_id)
            
            await credit_service.admin_adjust_credits(
                user_id=user_id,
                amount=data.amount,
                description=data.description,
                admin_email=admin_email,
            )
            
            new_balance = await credit_service.get_balance(user_id)
            
            results.append(BatchAdjustResult(
                user_id=user_id,
                success=True,
                new_balance=new_balance.get("total", 0),
            ))
            success_count += 1
        except ValueError as e:
            results.append(BatchAdjustResult(
                user_id=user_id,
                success=False,
                error=str(e),
            ))
            failure_count += 1
        except InsufficientCreditsError as e:
            results.append(BatchAdjustResult(
                user_id=user_id,
                success=False,
                error=str(e),
            ))
            failure_count += 1
        except Exception as e:
            results.append(BatchAdjustResult(
                user_id=user_id,
                success=False,
                error=f"Unexpected error: {str(e)}",
            ))
            failure_count += 1
    
    client_info = get_client_info(request)
    await audit_service.log_action(
        admin_id=admin_id,
        admin_email=admin_email,
        action=AuditAction.CREDIT_BATCH_ADJUST.value,
        resource_type="user",
        resource_id="batch",
        new_value={
            "user_ids": data.user_ids,
            "amount": data.amount,
            "description": data.description,
            "success_count": success_count,
            "failure_count": failure_count,
        },
        ip_address=client_info.get("ip_address"),
        user_agent=client_info.get("user_agent"),
    )
    
    return {
        "success": True,
        "message": f"Adjusted credits for {success_count} users ({failure_count} failures)",
        "success_count": success_count,
        "failure_count": failure_count,
        "results": [r.model_dump() for r in results],
    }


@router.post("/initialize")
async def initialize_default_data(
    request: Request,
    admin = Depends(get_admin_user)
) -> BaseResponse:
    await pricing_service.initialize_default_data()
    return BaseResponse(success=True, message="Default pricing data initialized")
