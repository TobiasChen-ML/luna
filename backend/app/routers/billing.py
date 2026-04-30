from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from typing import Any, Optional
import logging
import time
import hmac

from app.models import (
    BaseResponse, SubscriptionTier,
    USDTOrderCreate, CryptoOrderCreate, TelegramStarsOrderCreate,
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
STAR_USD_CENTS = 2.04


def _usd_cents_to_stars(price_cents: int) -> int:
    return max(1, int((int(price_cents) / STAR_USD_CENTS) + 0.5))


def _extract_order_id_from_telegram_payload(payload: dict[str, Any]) -> Optional[str]:
    direct_order_id = payload.get("order_id")
    if direct_order_id:
        return str(direct_order_id)

    candidates: list[Any] = [payload.get("payload")]

    successful_payment = payload.get("successful_payment")
    if isinstance(successful_payment, dict):
        candidates.append(successful_payment.get("invoice_payload"))

    pre_checkout_query = payload.get("pre_checkout_query")
    if isinstance(pre_checkout_query, dict):
        candidates.append(pre_checkout_query.get("invoice_payload"))

    message = payload.get("message")
    if isinstance(message, dict):
        message_payment = message.get("successful_payment")
        if isinstance(message_payment, dict):
            candidates.append(message_payment.get("invoice_payload"))

    for payload_value in candidates:
        if isinstance(payload_value, str):
            if payload_value.startswith("stars:"):
                return payload_value.split(":", 1)[1]
            if payload_value:
                return payload_value

    return None


def _normalize_stars_status(payload: dict[str, Any]) -> str:
    status = payload.get("status")
    if status:
        return str(status).lower()

    successful_payment = payload.get("successful_payment")
    if isinstance(successful_payment, dict):
        return "paid"

    message = payload.get("message")
    if isinstance(message, dict) and isinstance(message.get("successful_payment"), dict):
        return "paid"

    pre_checkout_query = payload.get("pre_checkout_query")
    if isinstance(pre_checkout_query, dict):
        return "pre_checkout"

    return ""


def _normalize_crypto_status(payload: dict[str, Any]) -> str:
    raw_status = (
        payload.get("status")
        or payload.get("payment_status")
        or payload.get("state")
        or payload.get("event")
        or ""
    )
    status = str(raw_status).lower()
    if status in {"confirmed", "completed", "complete", "paid", "success", "payment_success"}:
        return "paid"
    if status in {"failed", "error", "expired", "timeout"}:
        return "failed"
    if status in {"cancelled", "canceled"}:
        return "cancelled"
    return status


def _extract_crypto_order_refs(payload: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    order_id = (
        payload.get("order_id")
        or payload.get("merchant_order_id")
        or payload.get("client_order_id")
        or metadata.get("order_id")
    )
    provider_order_id = (
        payload.get("provider_order_id")
        or payload.get("payment_id")
        or payload.get("invoice_id")
        or payload.get("id")
    )
    return (str(order_id) if order_id else None, str(provider_order_id) if provider_order_id else None)


@router.get("/pricing")
async def get_pricing(request: Request) -> dict[str, Any]:
    config = await pricing_service.get_full_pricing_config()
    return config


@router.post("/subscriptions/checkout")
async def subscription_checkout(
    request: Request,
    data: dict[str, Any],
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    tier = str(data.get("tier") or "").lower()
    if tier not in {SubscriptionTier.PREMIUM.value, SubscriptionTier.PRO.value}:
        raise HTTPException(status_code=400, detail="tier must be premium or pro")

    billing_period = str(data.get("billing_period") or "month").lower()
    success_url = data.get("success_url")
    cancel_url = data.get("cancel_url")

    try:
        return await billing_svc.create_subscription_checkout(
            user_id=user.id,
            tier=tier,
            billing_period=billing_period,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/subscriptions/portal")
async def subscription_portal(
    request: Request,
    data: Optional[dict[str, Any]] = None,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    return_url = data.get("return_url") if isinstance(data, dict) else None
    portal_url = await billing_svc.get_subscription_portal_url(user.id, return_url=return_url)
    return {
        "portal_url": portal_url,
    }


@router.get("/subscriptions/current")
async def get_current_subscription(
    request: Request,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    return await billing_svc.get_current_subscription(user.id)


@router.post("/subscriptions/cancel")
async def cancel_subscription(
    request: Request,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    result = await billing_svc.cancel_subscription(user.id)
    status = result.get("status")
    if status == "scheduled":
        return {
            "success": True,
            "cancel_at": result.get("cancel_at"),
            "message": "Subscription cancellation scheduled",
        }
    return {
        "success": True,
        "cancel_at": None,
        "message": "No active subscription to cancel",
    }


@router.post("/subscriptions/reactivate")
async def reactivate_subscription(
    request: Request,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    result = await billing_svc.reactivate_subscription(user.id)
    status = result.get("status")
    if status == "reactivated":
        return {"success": True, "message": "Subscription reactivated"}
    return {"success": True, "message": "No active subscription to reactivate"}


@router.get("/credit-packs")
async def get_credit_packs(request: Request) -> dict[str, Any]:
    packs = await pricing_service.get_credit_packs(active_only=True)
    return {
        "packs": [p.to_dict() for p in packs]
    }


@router.post("/credit-packs/checkout")
async def credit_pack_checkout(
    request: Request,
    data: dict[str, Any],
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    pack_id = str(data.get("pack_id") or "").strip()
    if not pack_id:
        raise HTTPException(status_code=400, detail="pack_id is required")
    success_url = data.get("success_url")
    cancel_url = data.get("cancel_url")

    try:
        return await billing_svc.create_credit_pack_checkout(
            user_id=user.id,
            pack_id=pack_id,
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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
async def get_billing_history(
    request: Request,
    user = Depends(get_current_user_required),
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    return await billing_svc.get_billing_history(
        user_id=user.id,
        limit=limit,
        offset=offset,
    )


@router.post("/usdt/orders")
async def create_usdt_order(
    request: Request,
    data: USDTOrderCreate,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    if data.pack_id:
        return await billing_svc.create_crypto_order(
            user_id=user.id,
            asset="USDT",
            network=data.network or "POLYGON",
            product_type="credit_pack",
            pack_id=data.pack_id,
            metadata=data.metadata,
        )

    credits = data.credits
    if credits is None and data.product_id.startswith("credits_"):
        try:
            credits = int(data.product_id.split("_", 1)[1])
        except (TypeError, ValueError):
            credits = None
    if not credits or credits <= 0:
        raise HTTPException(status_code=400, detail="credits or pack_id is required")

    return await billing_svc.create_usdt_order(
        user_id=user.id,
        amount=float(data.amount),
        credits=int(credits),
    )


@router.get("/usdt/orders/{order_id}")
async def get_usdt_order(
    request: Request,
    order_id: str,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    order = await billing_svc.get_usdt_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return BillingService._crypto_order_response(order)


@router.post("/usdt/orders/{order_id}/submit", response_model=BaseResponse)
async def submit_usdt_order(
    request: Request,
    order_id: str,
    data: dict[str, Any] | None = None,
    user = Depends(get_current_user_required),
) -> BaseResponse:
    order = await billing_svc.get_usdt_order(order_id)
    if not order or order.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    tx_hash = (data or {}).get("tx_hash") or (data or {}).get("transaction_hash")
    if not tx_hash:
        raise HTTPException(status_code=400, detail="tx_hash is required")
    await billing_svc.submit_usdt_order(order_id, str(tx_hash))
    return BaseResponse(success=True, message="USDT payment submitted")


@router.post("/usdt/orders/{order_id}/refresh")
async def refresh_usdt_order(
    request: Request,
    order_id: str,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    order = await billing_svc.get_usdt_order(order_id)
    if not order or order.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return BillingService._crypto_order_response(order)


@router.post("/crypto/orders")
async def create_crypto_order(
    request: Request,
    data: CryptoOrderCreate,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    try:
        return await billing_svc.create_crypto_order(
            user_id=user.id,
            asset=data.asset,
            network=data.network,
            product_type=data.product_type,
            pack_id=data.pack_id,
            tier=data.tier,
            billing_period=data.billing_period,
            metadata=data.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/crypto/orders/{order_id}")
async def get_crypto_order(
    request: Request,
    order_id: str,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    order = await billing_svc.get_crypto_order(order_id)
    if not order or order.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    return BillingService._crypto_order_response(order)


@router.post("/crypto/orders/{order_id}/submit", response_model=BaseResponse)
async def submit_crypto_order(
    request: Request,
    order_id: str,
    data: dict[str, Any] | None = None,
    user = Depends(get_current_user_required),
) -> BaseResponse:
    order = await billing_svc.get_crypto_order(order_id)
    if not order or order.get("user_id") != user.id:
        raise HTTPException(status_code=404, detail="Order not found")
    tx_hash = (data or {}).get("tx_hash") or (data or {}).get("transaction_hash")
    if not tx_hash:
        raise HTTPException(status_code=400, detail="tx_hash is required")
    await billing_svc.submit_usdt_order(order_id, str(tx_hash))
    return BaseResponse(success=True, message="Crypto payment submitted")


@router.post("/telegram-stars/orders")
async def create_telegram_stars_order(
    request: Request, 
    data: TelegramStarsOrderCreate,
    user = Depends(get_current_user_required),
) -> dict[str, Any]:
    amount_stars = data.amount_stars if data.amount_stars is not None else data.amount

    metadata = dict(data.metadata or {})
    pack_key = data.pack_id or data.product_id
    product_type = (data.product_type or metadata.get("product_type") or metadata.get("product") or "").lower()
    tier = (data.tier or metadata.get("tier") or "").lower()
    billing_period = (
        data.billing_period
        or metadata.get("billing_period")
        or metadata.get("period")
        or ""
    )
    billing_period = str(billing_period).lower()

    if not product_type and pack_key and str(pack_key).startswith("subscription_"):
        product_type = "subscription"
    if not product_type:
        product_type = "credit_pack"

    credits = data.credits
    if product_type == "subscription":
        if not tier:
            tier = SubscriptionTier.PREMIUM.value
        if tier not in {SubscriptionTier.PREMIUM.value, SubscriptionTier.PRO.value}:
            raise HTTPException(status_code=400, detail="tier must be premium or pro")
        if billing_period not in {"1m", "3m", "12m", "month", "quarter", "year"}:
            raise HTTPException(status_code=400, detail="billing_period must be 1m, 3m, 12m, month, quarter, or year")
        period_map = {"month": "1m", "quarter": "3m", "year": "12m"}
        billing_period = period_map.get(billing_period, billing_period)
        plan = await pricing_service.get_subscription_plan(billing_period)
        if not plan or not plan.is_active:
            raise HTTPException(status_code=400, detail="subscription plan not available")
        amount_stars = _usd_cents_to_stars(plan.price_cents)
        config = await credit_service.get_config()
        credits = int(float(config.get("premium_monthly_credits", 100) or 100))
    else:
        matched = None
        if pack_key:
            packs = await pricing_service.get_credit_packs(active_only=True)
            pack_map = {p.pack_id: p for p in packs}
            matched = pack_map.get(pack_key)
            if matched:
                credits = int((matched.credits or 0) + (matched.bonus_credits or 0))
                price_cents = getattr(matched, "price_cents", None)
                if price_cents is not None:
                    amount_stars = _usd_cents_to_stars(price_cents)
            elif credits is None and pack_key.startswith("credits_"):
                # Backward-compatible fallback for legacy product ids like credits_50.
                try:
                    credits = int(pack_key.split("_", 1)[1])
                except (TypeError, ValueError):
                    credits = None
    if credits is None or credits <= 0:
        raise HTTPException(status_code=400, detail="credits is required and must be > 0")
    if amount_stars is None:
        raise HTTPException(status_code=400, detail="amount_stars (or amount) is required")

    metadata.update(
        {
            "product_type": product_type,
            "tier": tier or None,
            "billing_period": billing_period or None,
        }
    )

    try:
        result = await billing_svc.create_telegram_stars_order(
            user_id=user.id,
            amount_stars=int(amount_stars),
            credits=int(credits),
            pack_id=data.pack_id or data.product_id,
            product_type=product_type,
            tier=tier or None,
            billing_period=billing_period or None,
            title=data.title,
            description=data.description,
            metadata=metadata,
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
        "product_type": order.get("product_type", "credit_pack"),
        "tier": order.get("tier"),
        "billing_period": order.get("billing_period"),
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


async def _process_crypto_webhook_payload(payload: dict[str, Any]) -> BaseResponse:
    status = _normalize_crypto_status(payload)
    order_id, provider_order_id = _extract_crypto_order_refs(payload)
    resolved_order_id = await billing_svc.resolve_crypto_order_id(order_id, provider_order_id)
    tx_hash = payload.get("tx_hash") or payload.get("transaction_hash") or payload.get("hash")

    if resolved_order_id:
        if status == "paid":
            result = await billing_svc.mark_crypto_order_paid(
                order_id=resolved_order_id,
                charge_id=str(tx_hash or provider_order_id or ""),
                webhook_payload=payload,
            )
            logger.info(f"Crypto payment success: order_id={resolved_order_id}, result={result}")
        elif status == "failed":
            await billing_svc.mark_crypto_order_failed(resolved_order_id, webhook_payload=payload)
        elif status == "cancelled":
            await billing_svc.mark_crypto_order_cancelled(resolved_order_id, webhook_payload=payload)
        logger.info(f"Crypto webhook processed: order_id={resolved_order_id}, status={status}")
        return BaseResponse(success=True, message=f"Crypto webhook processed: {status or 'unknown'}")

    # Legacy fallback for providers that post full user/credit data without a cached order.
    user_id = payload.get("user_id")
    try:
        credits = int(payload.get("credits", 0))
    except (TypeError, ValueError):
        logger.warning(f"Crypto webhook invalid credits value: {payload.get('credits')}")
        raise HTTPException(status_code=400, detail="Invalid credits value")

    if credits <= 0 or credits > MAX_CREDITS_PER_TRANSACTION:
        logger.warning(f"Crypto webhook credits out of bounds: {credits}")
        raise HTTPException(status_code=400, detail="Credits amount out of allowed range")

    if status == "paid" and user_id:
        asset = str(payload.get("asset") or payload.get("currency") or "USDT").upper()
        network = str(payload.get("network") or "").upper()
        order_ref = str(tx_hash or provider_order_id or order_id or "")
        await credit_service.add_credits(
            user_id=user_id,
            amount=credits,
            transaction_type="purchase",
            credit_source="purchased",
            order_id=order_ref,
            description=f"Purchased {credits} credits via {asset}{f' {network}' if network else ''}",
        )

    logger.info(f"Crypto webhook processed via legacy fallback: tx_hash={tx_hash}, status={status}")
    return BaseResponse(success=True, message=f"Crypto webhook processed: {status or 'unknown'}")


@router.post("/webhooks/crypto", response_model=BaseResponse)
async def crypto_webhook(
    request: Request,
    x_webhook_signature: str = Header(None, alias="X-Webhook-Signature"),
) -> BaseResponse:
    try:
        payload = await request.json()

        if not x_webhook_signature:
            logger.warning("Crypto webhook missing signature header")
            raise HTTPException(status_code=401, detail="Missing signature")

        from app.core.config import get_config_value, get_settings
        settings = get_settings()
        secret = (
            await get_config_value("CRYPTO_PAYMENT_GATEWAY_WEBHOOK_SECRET")
            or await get_config_value("USDT_WEBHOOK_SECRET")
            or settings.ccbill_client_secret
        )
        if not secret:
            logger.error("Crypto webhook secret not configured")
            raise HTTPException(status_code=503, detail="Webhook processing unavailable")

        if not webhook_service.verify_usdt_signature(payload, x_webhook_signature, secret):
            logger.warning("Crypto webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")

        event_time = payload.get("timestamp", 0)
        if event_time and abs(time.time() - event_time) > WEBHOOK_TIMESTAMP_TOLERANCE:
            logger.warning("Crypto webhook timestamp outside tolerance window")
            raise HTTPException(status_code=400, detail="Webhook expired")

        return await _process_crypto_webhook_payload(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Crypto webhook error: {e}")
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

        payload.setdefault("asset", "USDT")
        return await _process_crypto_webhook_payload(payload)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"USDT webhook error: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")


@router.post("/webhooks/telegram-stars", response_model=BaseResponse)
async def telegram_stars_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None, alias="X-Telegram-Bot-Api-Secret-Token"),
) -> BaseResponse:
    try:
        payload = await request.json()
        
        from app.core.config import get_config_value, get_settings
        settings = get_settings()
        bot_token = await get_config_value("TELEGRAM_BOT_TOKEN") or settings.telegram_bot_token
        
        if not bot_token:
            logger.error("Telegram bot token not configured")
            raise HTTPException(status_code=503, detail="Webhook processing unavailable")
        
        webhook_secret = (
            await get_config_value("TELEGRAM_WEBHOOK_SECRET_TOKEN")
            or await get_config_value("TELEGRAM_STAR_GATEWAY_WEBHOOK_AUTH_TOKEN")
            or await get_config_value("TELEGRAM_BOT_WEBHOOK_SECRET")
        )
        if webhook_secret:
            if not x_telegram_bot_api_secret_token:
                logger.warning("Telegram Stars webhook missing secret token header")
                raise HTTPException(status_code=401, detail="Missing secret token")
            if not hmac.compare_digest(x_telegram_bot_api_secret_token, webhook_secret):
                logger.warning("Telegram Stars webhook secret token verification failed")
                raise HTTPException(status_code=401, detail="Invalid secret token")
        elif not webhook_service.verify_telegram_signature(payload, bot_token):
            logger.warning("Telegram Stars webhook signature verification failed")
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        auth_date = payload.get("auth_date", 0)
        if auth_date and abs(time.time() - auth_date) > WEBHOOK_TIMESTAMP_TOLERANCE:
            logger.warning("Telegram Stars webhook timestamp outside tolerance window")
            raise HTTPException(status_code=400, detail="Webhook expired")

        status = _normalize_stars_status(payload)
        order_id = _extract_order_id_from_telegram_payload(payload)
        charge_id = payload.get("charge_id") or payload.get("payment_id")
        successful_payment = payload.get("successful_payment")
        pre_checkout_query = payload.get("pre_checkout_query")
        message = payload.get("message")
        if not isinstance(successful_payment, dict) and isinstance(message, dict):
            nested_payment = message.get("successful_payment")
            if isinstance(nested_payment, dict):
                successful_payment = nested_payment
        if isinstance(successful_payment, dict):
            charge_id = (
                charge_id
                or successful_payment.get("telegram_payment_charge_id")
                or successful_payment.get("provider_payment_charge_id")
            )
        if status == "pre_checkout":
            if not isinstance(pre_checkout_query, dict):
                raise HTTPException(status_code=400, detail="pre_checkout_query required")

            pre_checkout_query_id = pre_checkout_query.get("id")
            if not pre_checkout_query_id:
                raise HTTPException(status_code=400, detail="pre_checkout_query id required")

            if not order_id:
                await billing_svc.answer_telegram_pre_checkout_query(
                    pre_checkout_query_id=str(pre_checkout_query_id),
                    ok=False,
                    error_message="Payment order is missing.",
                )
                raise HTTPException(status_code=400, detail="order_id required")

            order = await billing_svc.get_telegram_stars_order(order_id)
            expected_amount = int(order.get("amount_stars", 0)) if order else 0
            actual_amount = int(pre_checkout_query.get("total_amount", 0) or 0)
            currency = str(pre_checkout_query.get("currency") or "").upper()
            if not order or order.get("status") != "pending":
                await billing_svc.answer_telegram_pre_checkout_query(
                    pre_checkout_query_id=str(pre_checkout_query_id),
                    ok=False,
                    error_message="Payment order is no longer available.",
                )
            elif currency and currency != "XTR":
                await billing_svc.answer_telegram_pre_checkout_query(
                    pre_checkout_query_id=str(pre_checkout_query_id),
                    ok=False,
                    error_message="Unsupported payment currency.",
                )
            elif actual_amount and actual_amount != expected_amount:
                await billing_svc.answer_telegram_pre_checkout_query(
                    pre_checkout_query_id=str(pre_checkout_query_id),
                    ok=False,
                    error_message="Payment amount does not match this order.",
                )
            else:
                await billing_svc.answer_telegram_pre_checkout_query(
                    pre_checkout_query_id=str(pre_checkout_query_id),
                    ok=True,
                )

            logger.info(f"Telegram Stars pre-checkout processed: order_id={order_id}")
            return BaseResponse(success=True, message="Telegram Stars pre-checkout processed")

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
        elif status in ["refunded", "refund", "chargeback", "reversed"]:
            await billing_svc.mark_telegram_stars_order_refunded(order_id=order_id, webhook_payload=payload)

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
