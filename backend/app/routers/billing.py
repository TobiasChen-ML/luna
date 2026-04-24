from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from typing import Any, Optional
import logging
import time

from app.models import (
    BaseResponse, SubscriptionTier, SubscriptionCheckoutRequest,
    CreditPackCheckoutRequest, USDTOrderCreate, TelegramStarsOrderCreate,
    OrderStatus
)
from app.services.auth_service import webhook_service
from app.services.pricing_service import pricing_service
from app.services.credit_service import credit_service
from app.services.billing_service import BillingService
from app.core.dependencies import get_current_user_required

router = APIRouter(prefix="/api/billing", tags=["billing"])
logger = logging.getLogger(__name__)
billing_svc = BillingService()

WEBHOOK_TIMESTAMP_TOLERANCE = 300


MAX_CREDITS_PER_TRANSACTION = 10000


def _extract_order_id_from_telegram_payload(payload: dict[str, Any]) -> Optional[str]:
    direct_order_id = payload.get("order_id")
    if direct_order_id:
        return str(direct_order_id)

    payload_value = payload.get("payload")
    if isinstance(payload_value, str):
        if payload_value.startswith("stars:"):
            return payload_value.split(":", 1)[1]
        return payload_value

    return None


@router.get("/pricing")
async def get_pricing(request: Request) -> dict[str, Any]:
    config = await pricing_service.get_full_pricing_config()
    return config


@router.post("/subscriptions/checkout")
async def subscription_checkout(
    request: Request, 
    data: SubscriptionCheckoutRequest
) -> dict[str, Any]:
    return {
        "checkout_url": "https://checkout.example.com/session_xyz",
        "session_id": "checkout_session_001",
    }


@router.post("/subscriptions/portal")
async def subscription_portal(request: Request) -> dict[str, Any]:
    return {
        "portal_url": "https://portal.example.com/manage",
    }


@router.get("/subscriptions/current")
async def get_current_subscription(request: Request) -> dict[str, Any]:
    return {
        "tier": "premium",
        "status": "active",
        "current_period_end": datetime.now().isoformat(),
        "cancel_at_period_end": False,
    }


@router.post("/subscriptions/cancel", response_model=BaseResponse)
async def cancel_subscription(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="Subscription cancellation scheduled")


@router.post("/subscriptions/reactivate", response_model=BaseResponse)
async def reactivate_subscription(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="Subscription reactivated")


@router.get("/credit-packs")
async def get_credit_packs(request: Request) -> dict[str, Any]:
    packs = await pricing_service.get_credit_packs(active_only=True)
    return {
        "packs": [p.to_dict() for p in packs]
    }


@router.post("/credit-packs/checkout")
async def credit_pack_checkout(
    request: Request, 
    data: CreditPackCheckoutRequest
) -> dict[str, Any]:
    return {
        "checkout_url": "https://checkout.example.com/pack_xyz",
        "session_id": "pack_session_001",
    }


@router.get("/credits/balance")
async def get_credits_balance(
    request: Request,
    user = Depends(get_current_user_required)
) -> dict[str, Any]:
    balance = await credit_service.get_balance(user.id)
    return {
        "total": balance["total"],
        "purchased": balance["purchased"],
        "monthly": balance["monthly"],
        "subscription_tier": balance["subscription_tier"],
        "subscription_end": balance["subscription_end"].isoformat() if balance["subscription_end"] else None,
    }


@router.get("/credits/transactions")
async def get_credits_transactions(
    request: Request,
    user = Depends(get_current_user_required),
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    transactions = await credit_service.get_transactions(
        user_id=user.id,
        limit=limit,
        offset=offset,
    )
    return {
        "transactions": [t.to_dict() for t in transactions],
        "limit": limit,
        "offset": offset,
    }


@router.get("/history")
async def get_billing_history(request: Request) -> list[dict[str, Any]]:
    return [
        {
            "id": "txn_001",
            "type": "subscription",
            "amount": 9.99,
            "currency": "USD",
            "status": "paid",
            "created_at": datetime.now().isoformat(),
        }
    ]


@router.post("/usdt/orders")
async def create_usdt_order(request: Request, data: USDTOrderCreate) -> dict[str, Any]:
    return {
        "order_id": "usdt_order_001",
        "amount": data.amount,
        "status": OrderStatus.PENDING,
        "payment_address": "0x1234...abcd",
        "created_at": datetime.now().isoformat(),
    }


@router.get("/usdt/orders/{order_id}")
async def get_usdt_order(request: Request, order_id: str) -> dict[str, Any]:
    return {
        "order_id": order_id,
        "amount": 10.0,
        "status": OrderStatus.PENDING,
        "payment_address": "0x1234...abcd",
        "created_at": datetime.now().isoformat(),
    }


@router.post("/usdt/orders/{order_id}/submit", response_model=BaseResponse)
async def submit_usdt_order(request: Request, order_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="USDT payment submitted")


@router.post("/usdt/orders/{order_id}/refresh")
async def refresh_usdt_order(request: Request, order_id: str) -> dict[str, Any]:
    return {
        "order_id": order_id,
        "status": OrderStatus.PENDING,
        "confirmations": 2,
        "required_confirmations": 6,
    }


@router.post("/telegram-stars/orders")
async def create_telegram_stars_order(
    request: Request, 
    data: TelegramStarsOrderCreate,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    amount_stars = data.amount_stars if data.amount_stars is not None else data.amount
    if amount_stars is None:
        raise HTTPException(status_code=400, detail="amount_stars (or amount) is required")

    credits = data.credits
    if credits is None:
        pack_key = data.pack_id or data.product_id
        if pack_key:
            packs = await pricing_service.get_credit_packs(active_only=True)
            pack_map = {p.pack_id: p for p in packs}
            matched = pack_map.get(pack_key)
            if matched:
                credits = int((matched.credits or 0) + (matched.bonus_credits or 0))
            elif pack_key.startswith("credits_"):
                # Backward-compatible fallback for legacy product ids like credits_50.
                try:
                    credits = int(pack_key.split("_", 1)[1])
                except (TypeError, ValueError):
                    credits = None
    if credits is None or credits <= 0:
        raise HTTPException(status_code=400, detail="credits is required and must be > 0")

    try:
        result = await billing_svc.create_telegram_stars_order(
            user_id=user.id,
            amount_stars=int(amount_stars),
            credits=int(credits),
            pack_id=data.pack_id or data.product_id,
            title=data.title,
            description=data.description,
            metadata=data.metadata or {},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return result


@router.get("/telegram-stars/orders/{order_id}")
async def get_telegram_stars_order(
    request: Request,
    order_id: str,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    order = await billing_svc.get_telegram_stars_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    return {
        "order_id": order_id,
        "status": order.get("status", OrderStatus.PENDING),
        "amount": int(order.get("amount_stars", 0)),
        "credits": int(order.get("credits", 0)),
        "invoice_link": order.get("invoice_link"),
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at"),
        "raw": order,
    }


@router.post("/telegram-stars/orders/{order_id}/submit", response_model=BaseResponse)
async def submit_telegram_stars_order(
    request: Request,
    order_id: str,
    data: dict[str, Any] | None = None,
    user = Depends(get_current_user_required),
) -> BaseResponse:
    order = await billing_svc.get_telegram_stars_order(order_id)
    if not order or order.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    payment_id = (data or {}).get("payment_id") or (data or {}).get("charge_id") or f"manual_{order_id}"
    try:
        await billing_svc.submit_telegram_stars_order(order_id=order_id, payment_id=str(payment_id))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"submit_telegram_stars_order failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to submit Telegram Stars payment")

    return BaseResponse(success=True, message="Telegram Stars payment submitted")


@router.post("/telegram-stars/orders/{order_id}/invoice-link")
async def create_telegram_stars_invoice_link(
    request: Request, 
    order_id: str,
    data: dict[str, Any] | None = None,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    order = await billing_svc.get_telegram_stars_order(order_id)
    if not order or order.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        result = await billing_svc.create_telegram_stars_invoice_link(
            order_id=order_id,
            title=(data or {}).get("title"),
            description=(data or {}).get("description"),
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error(f"create_telegram_stars_invoice_link failed: {exc}")
        raise HTTPException(status_code=500, detail="Failed to create Telegram invoice link")


@router.post("/webhooks/stripe", response_model=BaseResponse)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
) -> BaseResponse:
    from app.services.billing_service import BillingService
    billing_svc = BillingService()
    
    try:
        payload = await request.body()
        
        if not stripe_signature:
            logger.warning("Stripe webhook missing signature header")
            raise HTTPException(status_code=401, detail="Missing signature")
        
        result = await billing_svc.handle_stripe_webhook(payload, stripe_signature)
        
        logger.info(f"Stripe webhook processed: {result.get('status')}")
        return BaseResponse(success=True, message=result.get("status", "processed"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/webhooks/ccbill", response_model=BaseResponse)
async def ccbill_webhook(
    request: Request,
    x_ccbill_signature: str = Header(None, alias="X-CCBill-Signature")
) -> BaseResponse:
    try:
        payload = await request.json()
        
        if not x_ccbill_signature:
            logger.warning("CCBill webhook missing signature header")
            raise HTTPException(status_code=401, detail="Missing signature")
        
        if not webhook_service.verify_ccbill_signature(payload, x_ccbill_signature):
            logger.warning("CCBill webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        event_time = payload.get("timestamp", 0)
        if event_time and abs(time.time() - event_time) > WEBHOOK_TIMESTAMP_TOLERANCE:
            logger.warning("CCBill webhook timestamp outside tolerance window")
            raise HTTPException(status_code=400, detail="Webhook expired")

        event_type = payload.get("event", "unknown")
        user_id = payload.get("user_id")
        try:
            credits = int(payload.get("credits", 0))
        except (TypeError, ValueError):
            logger.warning(f"CCBill webhook invalid credits value: {payload.get('credits')}")
            raise HTTPException(status_code=400, detail="Invalid credits value")
        
        if credits <= 0 or credits > MAX_CREDITS_PER_TRANSACTION:
            logger.warning(f"CCBill webhook credits out of bounds: {credits}")
            raise HTTPException(status_code=400, detail="Credits amount out of allowed range")
        
        order_id = payload.get("order_id") or payload.get("transaction_id")
        
        if event_type in ["payment_success", "RenewalSuccess", "NewSaleSuccess"]:
            if user_id and credits > 0:
                try:
                    await credit_service.add_credits(
                        user_id=user_id,
                        amount=credits,
                        transaction_type="purchase",
                        credit_source="purchased",
                        order_id=order_id,
                        description=f"Purchased {credits} credits via CCBill"
                    )
                    logger.info(f"CCBill payment success: {credits} credits added to user {user_id}")
                except Exception as e:
                    logger.error(f"CCBill credit add failed: {e}")
                    raise HTTPException(status_code=500, detail="Failed to add credits")
            else:
                logger.warning(f"CCBill webhook missing user_id or credits: {payload}")
        
        logger.info(f"CCBill webhook processed: {event_type}")
        return BaseResponse(success=True, message=f"CCBill webhook processed: {event_type}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CCBill webhook error: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")


@router.post("/webhooks/usdt", response_model=BaseResponse)
async def usdt_webhook(
    request: Request,
    x_webhook_signature: str = Header(None, alias="X-Webhook-Signature")
) -> BaseResponse:
    try:
        payload = await request.json()
        
        if not x_webhook_signature:
            logger.warning("USDT webhook missing signature header")
            raise HTTPException(status_code=401, detail="Missing signature")
        
        from app.core.config import get_config_value, get_settings
        settings = get_settings()
        secret = (
            await get_config_value("CCBILL_CLIENT_SECRET")
            or await get_config_value("USDT_WEBHOOK_SECRET")
            or settings.ccbill_client_secret
        )
        if not secret:
            logger.error("USDT webhook secret not configured")
            raise HTTPException(status_code=503, detail="Webhook processing unavailable")
        
        if not webhook_service.verify_usdt_signature(payload, x_webhook_signature, secret):
            logger.warning("USDT webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        event_time = payload.get("timestamp", 0)
        if event_time and abs(time.time() - event_time) > WEBHOOK_TIMESTAMP_TOLERANCE:
            logger.warning("USDT webhook timestamp outside tolerance window")
            raise HTTPException(status_code=400, detail="Webhook expired")

        status = payload.get("status", "")
        user_id = payload.get("user_id")
        try:
            credits = int(payload.get("credits", 0))
        except (TypeError, ValueError):
            logger.warning(f"USDT webhook invalid credits value: {payload.get('credits')}")
            raise HTTPException(status_code=400, detail="Invalid credits value")
        
        if credits <= 0 or credits > MAX_CREDITS_PER_TRANSACTION:
            logger.warning(f"USDT webhook credits out of bounds: {credits}")
            raise HTTPException(status_code=400, detail="Credits amount out of allowed range")
        
        tx_hash = payload.get("tx_hash")
        
        if status == "confirmed":
            if user_id and credits > 0:
                try:
                    await credit_service.add_credits(
                        user_id=user_id,
                        amount=credits,
                        transaction_type="purchase",
                        credit_source="purchased",
                        order_id=tx_hash,
                        description=f"Purchased {credits} credits via USDT (tx: {tx_hash})"
                    )
                    logger.info(f"USDT payment confirmed: {credits} credits added to user {user_id}")
                except Exception as e:
                    logger.error(f"USDT credit add failed: {e}")
                    raise HTTPException(status_code=500, detail="Failed to add credits")
            else:
                logger.warning(f"USDT webhook missing user_id or credits: {payload}")
        
        logger.info(f"USDT webhook processed: tx_hash={tx_hash}, status={status}")
        return BaseResponse(success=True, message=f"USDT webhook processed: {status}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"USDT webhook error: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")


@router.post("/webhooks/telegram-stars", response_model=BaseResponse)
async def telegram_stars_webhook(
    request: Request
) -> BaseResponse:
    try:
        payload = await request.json()
        
        from app.core.config import get_config_value, get_settings
        settings = get_settings()
        bot_token = await get_config_value("TELEGRAM_BOT_TOKEN") or settings.telegram_bot_token
        
        if not bot_token:
            logger.error("Telegram bot token not configured")
            raise HTTPException(status_code=503, detail="Webhook processing unavailable")
        
        if not webhook_service.verify_telegram_signature(payload, bot_token):
            logger.warning("Telegram Stars webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        auth_date = payload.get("auth_date", 0)
        if auth_date and abs(time.time() - auth_date) > WEBHOOK_TIMESTAMP_TOLERANCE:
            logger.warning("Telegram Stars webhook timestamp outside tolerance window")
            raise HTTPException(status_code=400, detail="Webhook expired")

        status = str(payload.get("status", "")).lower()
        order_id = _extract_order_id_from_telegram_payload(payload)
        charge_id = payload.get("charge_id") or payload.get("payment_id")
        if not order_id:
            logger.warning(f"Telegram Stars webhook missing order_id/payload: {payload}")
            raise HTTPException(status_code=400, detail="order_id required")

        if status in ["paid", "successful"]:
            try:
                result = await billing_svc.mark_telegram_stars_order_paid(
                    order_id=order_id,
                    charge_id=str(charge_id) if charge_id else None,
                    webhook_payload=payload,
                )
                logger.info(f"Telegram Stars payment success: order_id={order_id}, result={result}")
            except ValueError as e:
                # Backward-compatible fallback: if order cache is missing, use webhook payload directly.
                user_id = payload.get("user_id")
                try:
                    credits = int(payload.get("credits", 0))
                except (TypeError, ValueError):
                    credits = 0
                if user_id and credits > 0 and "not found" in str(e).lower():
                    from app.models.credit_transaction import CreditTransaction
                    with billing_svc.db.transaction() as session:
                        existing_tx = (
                            session.query(CreditTransaction)
                            .filter(
                                CreditTransaction.user_id == user_id,
                                CreditTransaction.order_id == order_id,
                                CreditTransaction.transaction_type == "purchase",
                            )
                            .first()
                        )
                    if not existing_tx:
                        await credit_service.add_credits(
                            user_id=user_id,
                            amount=credits,
                            transaction_type="purchase",
                            credit_source="purchased",
                            order_id=order_id,
                            description=f"Purchased {credits} credits via Telegram Stars (legacy fallback)",
                        )
                    logger.warning(
                        f"Telegram Stars order {order_id} missing in cache; applied legacy fallback credit grant"
                    )
                else:
                    logger.warning(f"Telegram Stars paid webhook rejected for order {order_id}: {e}")
                    raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Telegram Stars paid webhook processing failed: {e}")
                raise HTTPException(status_code=500, detail="Failed to process Telegram Stars payment")
        elif status in ["failed", "error"]:
            await billing_svc.mark_telegram_stars_order_failed(order_id=order_id, webhook_payload=payload)
        elif status in ["cancelled", "canceled"]:
            await billing_svc.mark_telegram_stars_order_cancelled(order_id=order_id, webhook_payload=payload)

        logger.info(f"Telegram Stars webhook processed: order_id={order_id}, status={status}")
        return BaseResponse(success=True, message=f"Telegram Stars webhook processed: {status or 'unknown'}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telegram Stars webhook error: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")


@router.post("/admin/seed-credit-packs", response_model=BaseResponse)
async def seed_credit_packs(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="Credit packs seeded")
