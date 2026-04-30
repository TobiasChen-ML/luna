import logging
import stripe
from datetime import datetime, timedelta
from typing import Optional, Any
import uuid
import json
import urllib.request
import urllib.error
import asyncio

from ..core.config import BACKEND_DIR, get_settings, get_config_value
from .redis_service import RedisService
from .database_service import DatabaseService

logger = logging.getLogger(__name__)


TELEGRAM_STARS_ORDER_TTL_SECONDS = 86400 * 7
CRYPTO_ORDER_TTL_SECONDS = 86400 * 7
CRYPTO_PAYMENT_ASSETS = {"USDT", "USDC"}
CRYPTO_PAYMENT_NETWORKS_BY_ASSET = {
    "USDT": {"POLYGON"},
    "USDC": {"POLYGON"},
}
CRYPTO_PAYMENT_NETWORKS = set().union(*CRYPTO_PAYMENT_NETWORKS_BY_ASSET.values())


class BillingService:
    def __init__(
        self,
        redis: Optional[RedisService] = None,
        db: Optional[DatabaseService] = None,
    ):
        self.settings = get_settings()
        self.redis = redis or RedisService()
        self.db = db or DatabaseService()
        
    CREDIT_PACKS = {
        "small": {"credits": 100, "price": 4.99, "bonus": 0},
        "medium": {"credits": 500, "price": 19.99, "bonus": 50},
        "large": {"credits": 1500, "price": 49.99, "bonus": 200},
    }

    SUBSCRIPTION_TIERS = {
        "premium": {"price": 14.99, "credits": 500, "bonus_monthly": 100},
        "pro": {"price": 29.99, "credits": 1500, "bonus_monthly": 300},
    }

    async def _configure_stripe(self) -> Optional[str]:
        key = await get_config_value("STRIPE_SECRET_KEY", self.settings.stripe_secret_key)
        if key:
            stripe.api_key = key
        return key

    async def get_pricing(self) -> dict:
        return {
            "credit_packs": self.CREDIT_PACKS,
            "subscriptions": self.SUBSCRIPTION_TIERS,
        }

    async def get_credit_balance(self, user_id: str) -> dict:
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.firebase_uid == user_id).first()
            
            if not user:
                return {"credits": 0, "subscription_tier": None}
            
            return {
                "credits": user.credits,
                "subscription_tier": user.subscription_tier,
                "next_refill_hours": self._calculate_next_refill(user),
            }

    def _calculate_next_refill(self, user) -> Optional[int]:
        if user.subscription_tier == "free":
            return None
        
        if user.last_refill_at:
            next_refill = user.last_refill_at + timedelta(days=30)
            hours = max(0, int((next_refill - datetime.utcnow()).total_seconds() / 3600))
            return hours
        return None

    async def create_checkout_session(
        self,
        user_id: str,
        pack_type: Optional[str] = None,
        tier: Optional[str] = None,
        success_url: str = "",
        cancel_url: str = "",
        provider: str = "stripe",
    ) -> dict:
        if provider == "stripe":
            return await self._stripe_checkout(user_id, pack_type, tier, success_url, cancel_url)
        elif provider == "ccbill":
            return await self._ccbill_checkout(user_id, pack_type, tier)
        else:
            raise ValueError(f"Unknown payment provider: {provider}")

    async def _stripe_checkout(
        self,
        user_id: str,
        pack_type: Optional[str],
        tier: Optional[str],
        success_url: str,
        cancel_url: str,
    ) -> dict:
        await self._configure_stripe()
        if pack_type:
            pack = self.CREDIT_PACKS.get(pack_type)
            if not pack:
                raise ValueError(f"Invalid pack type: {pack_type}")
            
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"{pack['credits']} Credits Pack",
                            },
                            "unit_amount": int(pack["price"] * 100),
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "pack_type": pack_type,
                    "credits": pack["credits"] + pack["bonus"],
                },
            )
            
            return {
                "checkout_url": session.url,
                "session_id": session.id,
            }
        
        elif tier:
            sub = self.SUBSCRIPTION_TIERS.get(tier)
            if not sub:
                raise ValueError(f"Invalid tier: {tier}")
            
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"{tier.capitalize()} Subscription",
                            },
                            "unit_amount": int(sub["price"] * 100),
                            "recurring": {
                                "interval": "month",
                            },
                        },
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "tier": tier,
                    "monthly_credits": sub["credits"] + sub["bonus_monthly"],
                },
            )
            
            return {
                "checkout_url": session.url,
                "session_id": session.id,
            }
        
        raise ValueError("Must specify pack_type or tier")

    async def _ccbill_checkout(
        self,
        user_id: str,
        pack_type: Optional[str],
        tier: Optional[str],
    ) -> dict:
        from app.core.config import get_config_value
        client_id = await get_config_value("CCBILL_CLIENT_ID") or self.settings.ccbill_client_id
        return {
            "checkout_url": f"https://ccbill.com/checkout?client_id={client_id}",
            "session_id": str(uuid.uuid4()),
        }

    async def handle_stripe_webhook(self, payload: bytes, signature: str) -> dict:
        await self._configure_stripe()
        webhook_secret = await get_config_value("STRIPE_WEBHOOK_SECRET", self.settings.stripe_webhook_secret)
        if webhook_secret:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                webhook_secret,
            )
        else:
            event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
        
        event_type = event.get("type")
        data = event.get("data", {}).get("object", {})
        
        if event_type == "checkout.session.completed":
            return await self._handle_checkout_completed(data)
        elif event_type == "invoice.payment_succeeded":
            return await self._handle_subscription_payment(data)
        elif event_type == "invoice.paid":
            return await self._handle_subscription_payment(data)
        elif event_type == "customer.subscription.created":
            return await self._handle_subscription_created(data)
        elif event_type == "customer.subscription.updated":
            return await self._handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            return await self._handle_subscription_cancelled(data)
        elif event_type == "charge.refunded":
            return await self._handle_charge_refunded(data)
        
        return {"status": "ignored", "event_type": event_type}

    async def _handle_checkout_completed(self, session_data: dict) -> dict:
        from .credit_service import credit_service
        
        metadata = session_data.get("metadata", {})
        user_id = metadata.get("user_id")
        
        if not user_id:
            logger.error("Stripe webhook: No user_id in metadata")
            return {"status": "error", "message": "No user_id in metadata"}
        
        mode = session_data.get("mode", "payment")
        
        if mode == "subscription":
            tier = metadata.get("tier", "premium")
            monthly_credits = int(metadata.get("monthly_credits", 100))
            
            subscription_id = session_data.get("subscription")
            customer_id = session_data.get("customer")
            
            with self.db.get_session() as db_session:
                from ..models.user import User
                user = db_session.query(User).filter(User.id == user_id).first()
                
                if user:
                    user.tier = tier
                    user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
                    user.subscription_start_date = datetime.utcnow()
                    user.subscription_period = "1m"
                    if customer_id:
                        user.stripe_customer_id = customer_id
                    db_session.commit()
                    
                    try:
                        await credit_service.add_credits(
                            user_id=user.id,
                            amount=monthly_credits,
                            transaction_type="subscription",
                            credit_source="monthly",
                            description=f"Subscription started: {tier} tier"
                        )
                    except Exception as e:
                        logger.error(f"Failed to add subscription credits: {e}")
            
            logger.info(f"Subscription checkout completed for user {user_id}, tier: {tier}")
            return {"status": "success", "tier": tier, "credits_added": monthly_credits}
        
        else:
            credits = int(metadata.get("credits", 0))
            if credits <= 0:
                return {"status": "error", "message": "Invalid credits amount"}
            
            with self.db.get_session() as db_session:
                from ..models.user import User
                user = db_session.query(User).filter(User.id == user_id).first()
                
                if user:
                    try:
                        await credit_service.add_credits(
                            user_id=user.id,
                            amount=credits,
                            transaction_type="purchase",
                            credit_source="purchased",
                            order_id=session_data.get("payment_intent"),
                            description=f"Purchased {credits} credits"
                        )
                    except Exception as e:
                        logger.error(f"Failed to add purchased credits: {e}")
                        return {"status": "error", "message": str(e)}
            
            logger.info(f"Credit pack purchase completed for user {user_id}, credits: {credits}")
            return {"status": "success", "credits_added": credits}

    async def _handle_subscription_created(self, subscription: dict) -> dict:
        customer_id = subscription.get("customer")
        status = subscription.get("status")
        
        if status not in ["active", "trialing"]:
            return {"status": "ignored", "reason": f"Status is {status}"}
        
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.stripe_customer_id == customer_id).first()
            
            if user:
                user.tier = "premium"
                user.subscription_start_date = datetime.utcnow()
                
                current_period_end = subscription.get("current_period_end")
                if current_period_end:
                    user.subscription_end_date = datetime.fromtimestamp(current_period_end)
                
                session.commit()
                logger.info(f"Subscription created for user {user.id}")
                return {"status": "success", "user_id": user.id}
        
        return {"status": "error", "message": "User not found"}

    async def _handle_subscription_updated(self, subscription: dict) -> dict:
        customer_id = subscription.get("customer")
        status = subscription.get("status")
        cancel_at_period_end = subscription.get("cancel_at_period_end", False)
        
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.stripe_customer_id == customer_id).first()
            
            if user:
                if status in ["active", "trialing"]:
                    current_period_end = subscription.get("current_period_end")
                    if current_period_end:
                        user.subscription_end_date = datetime.fromtimestamp(current_period_end)
                    
                    if cancel_at_period_end:
                        logger.info(f"Subscription for user {user.id} will cancel at period end")
                elif status in ["canceled", "unpaid", "past_due"]:
                    user.tier = "free"
                    logger.info(f"Subscription for user {user.id} is now {status}, downgraded to free")
                
                session.commit()
                return {"status": "success", "user_id": user.id}
        
        return {"status": "error", "message": "User not found"}

    async def _handle_subscription_payment(self, invoice: dict) -> dict:
        from .credit_service import credit_service
        
        customer_id = invoice.get("customer")
        subscription_id = invoice.get("subscription")
        
        if not customer_id:
            return {"status": "error", "message": "No customer_id in invoice"}
        
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.stripe_customer_id == customer_id).first()
            
            if not user:
                logger.warning(f"User not found for Stripe customer {customer_id}")
                return {"status": "error", "message": "User not found"}
            
            period_end = invoice.get("period_end") or invoice.get("lines", {}).get("data", [{}])[0].get("period", {}).get("end")
            if period_end:
                user.subscription_end_date = datetime.fromtimestamp(period_end)
            
            if user.tier == "free":
                user.tier = "premium"
            
            session.commit()
            
            config = await credit_service.get_config()
            monthly_credits = float(config.get("premium_monthly_credits", 100))
            
            try:
                await credit_service.add_credits(
                    user_id=user.id,
                    amount=monthly_credits,
                    transaction_type="subscription",
                    credit_source="monthly",
                    description="Monthly subscription credits"
                )
                user.last_monthly_credit_grant = datetime.utcnow()
                session.commit()
            except Exception as e:
                logger.error(f"Failed to grant monthly credits: {e}")
            
            logger.info(f"Subscription payment processed for user {user.id}")
            return {"status": "success", "user_id": user.id, "credits_added": monthly_credits}

    async def _handle_subscription_cancelled(self, subscription: dict) -> dict:
        customer_id = subscription.get("customer")
        
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.stripe_customer_id == customer_id).first()
            
            if user:
                user.tier = "free"
                user.subscription_end_date = None
                session.commit()
                logger.info(f"Subscription cancelled for user {user.id}, downgraded to free")
                return {"status": "cancelled", "user_id": user.id}
        
        return {"status": "error", "message": "User not found"}

    async def _handle_charge_refunded(self, charge: dict) -> dict:
        from .credit_service import credit_service
        
        payment_intent_id = charge.get("payment_intent")
        refund = charge.get("refunds", {}).get("data", [{}])[0] if charge.get("refunds") else {}
        refund_id = refund.get("id", "unknown")
        amount_refunded = charge.get("amount_refunded", 0) / 100
        refund_reason = refund.get("reason", "requested_by_customer")
        
        if not payment_intent_id:
            logger.warning("Charge refunded event missing payment_intent_id")
            return {"status": "ignored", "reason": "No payment_intent_id"}
        
        with self.db.get_session() as session:
            from ..models.credit_transaction import CreditTransaction
            from ..models.user import User
            
            original_transaction = session.query(CreditTransaction).filter(
                CreditTransaction.order_id == payment_intent_id,
                CreditTransaction.transaction_type == "purchase",
            ).first()
            
            if not original_transaction:
                logger.info(f"No purchase transaction found for payment_intent: {payment_intent_id}")
                return {"status": "ignored", "reason": "No matching purchase"}
            
            user_id = original_transaction.user_id
            credits_to_deduct = original_transaction.amount
            
            existing_refund = session.query(CreditTransaction).filter(
                CreditTransaction.order_id == payment_intent_id,
                CreditTransaction.transaction_type == "refund_deduction",
            ).first()
            
            if existing_refund:
                logger.info(f"Refund already processed for payment_intent: {payment_intent_id}")
                return {"status": "ignored", "reason": "Already processed"}
            
            user = session.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.error(f"User {user_id} not found for refund processing")
                return {"status": "error", "message": "User not found"}
            
            credits_to_deduct = min(credits_to_deduct, float(user.purchased_credits or 0))
            
            user.purchased_credits = float(user.purchased_credits or 0) - credits_to_deduct
            user.credits = float(user.monthly_credits or 0) + float(user.purchased_credits or 0)
            
            deduction_transaction = CreditTransaction(
                user_id=user.id,
                transaction_type="refund_deduction",
                amount=-credits_to_deduct,
                balance_after=user.credits,
                credit_source="purchased",
                order_id=payment_intent_id,
                description=f"Refund processed: {refund_reason} (refund_id: {refund_id})",
            )
            session.add(deduction_transaction)
            session.commit()
            
            logger.info(
                f"Refund processed for user {user_id}: "
                f"deducted {credits_to_deduct} credits, refund_id: {refund_id}"
            )
            
            return {
                "status": "success",
                "user_id": user_id,
                "credits_deducted": credits_to_deduct,
                "refund_id": refund_id,
            }

    async def create_crypto_order(
        self,
        user_id: str,
        asset: str,
        network: str,
        product_type: str = "credit_pack",
        pack_id: Optional[str] = None,
        tier: Optional[str] = None,
        billing_period: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        from .pricing_service import pricing_service
        from .credit_service import credit_service

        normalized_asset = (asset or "USDT").upper()
        normalized_network = (network or "POLYGON").upper()
        if normalized_asset not in CRYPTO_PAYMENT_ASSETS:
            raise ValueError("asset must be USDT or USDC")
        if normalized_network not in CRYPTO_PAYMENT_NETWORKS_BY_ASSET[normalized_asset]:
            raise ValueError(f"network must be POLYGON for {normalized_asset}")

        normalized_product_type = (product_type or "credit_pack").lower()
        if normalized_product_type not in {"credit_pack", "subscription"}:
            raise ValueError("product_type must be credit_pack or subscription")

        credits = 0
        amount_usd_cents = 0
        order_pack_id = pack_id
        normalized_tier = (tier or "premium").lower() if normalized_product_type == "subscription" else None
        normalized_period = (billing_period or "1m").lower() if normalized_product_type == "subscription" else None

        if normalized_product_type == "credit_pack":
            if not order_pack_id:
                raise ValueError("pack_id is required for credit_pack orders")
            pack = await pricing_service.get_credit_pack(order_pack_id)
            if not pack or not pack.is_active:
                raise ValueError("Credit pack not available")
            credits = int((pack.credits or 0) + (pack.bonus_credits or 0))
            amount_usd_cents = int(pack.price_cents or 0)
        else:
            period_map = {"month": "1m", "quarter": "3m", "year": "12m"}
            normalized_period = period_map.get(normalized_period or "1m", normalized_period or "1m")
            if normalized_period not in {"1m", "3m", "12m"}:
                raise ValueError("billing_period must be 1m, 3m, 12m, month, quarter, or year")
            plan = await pricing_service.get_subscription_plan(normalized_period)
            if not plan or not plan.is_active:
                raise ValueError("subscription plan not available")
            amount_usd_cents = int(plan.price_cents or 0)
            config = await credit_service.get_config()
            credits = int(float(config.get("premium_monthly_credits", 100) or 100))
            order_pack_id = f"subscription_{normalized_tier}_{normalized_period}"

        if credits <= 0 or amount_usd_cents <= 0:
            raise ValueError("Order has invalid amount or credits")

        order_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        expires_at = datetime.utcnow() + timedelta(hours=24)

        gateway_order = await self._create_crypto_gateway_order(
            order_id=order_id,
            user_id=user_id,
            asset=normalized_asset,
            network=normalized_network,
            amount_usd_cents=amount_usd_cents,
            credits=credits,
            product_type=normalized_product_type,
            pack_id=order_pack_id,
            tier=normalized_tier,
            billing_period=normalized_period,
            metadata=metadata or {},
        )

        amount_crypto = gateway_order.get("amount_crypto")
        if amount_crypto is None:
            # Stablecoin fallback for providers that return only fiat amount.
            amount_crypto = round(amount_usd_cents / 100, 2)

        provider_order_id = gateway_order.get("provider_order_id") or gateway_order.get("id") or order_id
        order = {
            "order_id": order_id,
            "provider_order_id": str(provider_order_id),
            "user_id": user_id,
            "asset": normalized_asset,
            "network": normalized_network,
            "amount_usd_cents": amount_usd_cents,
            "amount_crypto": amount_crypto,
            "credits": credits,
            "product_type": normalized_product_type,
            "pack_id": order_pack_id,
            "tier": normalized_tier,
            "billing_period": normalized_period,
            "status": gateway_order.get("status") or "pending",
            "payment_address": gateway_order.get("payment_address") or gateway_order.get("address"),
            "payment_uri": gateway_order.get("payment_uri"),
            "checkout_url": gateway_order.get("checkout_url") or gateway_order.get("payment_url"),
            "created_at": now,
            "updated_at": now,
            "expires_at": gateway_order.get("expires_at") or expires_at.isoformat(),
            "gateway_payload": gateway_order,
            "metadata": metadata or {},
            "credits_applied": False,
            "subscription_applied": False,
        }

        await self.redis.set_json(self._crypto_order_key(order_id), order, ex=CRYPTO_ORDER_TTL_SECONDS)
        await self.redis.set_json(
            self._crypto_provider_order_key(str(provider_order_id)),
            {"order_id": order_id},
            ex=CRYPTO_ORDER_TTL_SECONDS,
        )

        return self._crypto_order_response(order)

    async def create_usdt_order(
        self,
        user_id: str,
        amount: float,
        credits: int,
    ) -> dict:
        order_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        expires_at = datetime.utcnow() + timedelta(hours=24)
        gateway_order = await self._create_local_crypto_order(
            order_id=order_id,
            asset="USDT",
            network="POLYGON",
            amount_crypto=float(amount),
            expires_at=expires_at,
        )
        order = {
            "order_id": order_id,
            "provider_order_id": order_id,
            "user_id": user_id,
            "asset": "USDT",
            "network": "POLYGON",
            "amount_usd_cents": int(float(amount) * 100),
            "amount_crypto": float(amount),
            "credits": credits,
            "product_type": "credit_pack",
            "status": "pending",
            "payment_address": gateway_order.get("payment_address"),
            "payment_uri": gateway_order.get("payment_uri"),
            "created_at": now,
            "updated_at": now,
            "expires_at": expires_at.isoformat(),
            "gateway_payload": gateway_order,
            "credits_applied": False,
            "subscription_applied": False,
        }
        await self.redis.set_json(self._crypto_order_key(order_id), order, ex=CRYPTO_ORDER_TTL_SECONDS)
        return {
            "order_id": order_id,
            "amount": amount,
            "credits": credits,
            "wallet_address": order.get("payment_address"),
            "payment_address": order.get("payment_address"),
            "payment_uri": order.get("payment_uri"),
            "expires_at": expires_at.isoformat(),
        }

    async def get_crypto_order(self, order_id: str) -> Optional[dict[str, Any]]:
        return await self.redis.get_json(self._crypto_order_key(order_id))

    async def get_usdt_order(self, order_id: str) -> Optional[dict]:
        order = await self.get_crypto_order(order_id)
        if order:
            return order
        return await self.redis.get_json(f"usdt_order:{order_id}")

    async def submit_usdt_order(self, order_id: str, tx_hash: str) -> dict:
        order = await self.get_crypto_order(order_id)
        
        if not order:
            raise ValueError("Order not found")
        
        if order.get("status") != "pending":
            raise ValueError("Order already processed")
        
        order["status"] = "processing"
        order["tx_hash"] = tx_hash
        order["updated_at"] = datetime.utcnow().isoformat()
        
        await self.redis.set_json(self._crypto_order_key(order_id), order, ex=CRYPTO_ORDER_TTL_SECONDS)
        
        return {"order_id": order_id, "status": "processing"}

    async def mark_crypto_order_paid(
        self,
        order_id: str,
        charge_id: Optional[str] = None,
        webhook_payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        order = await self.get_crypto_order(order_id)
        if not order:
            raise ValueError("Order not found")
        label = f"{order.get('asset') or 'Crypto'} {order.get('network') or ''}".strip()
        return await self._mark_cached_payment_order_paid(
            order=order,
            order_id=order_id,
            cache_key=self._crypto_order_key(order_id),
            gateway_label=label,
            charge_id=charge_id,
            webhook_payload=webhook_payload,
        )

    async def mark_crypto_order_failed(
        self,
        order_id: str,
        webhook_payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return await self._set_crypto_order_terminal_state(order_id, "failed", webhook_payload)

    async def mark_crypto_order_cancelled(
        self,
        order_id: str,
        webhook_payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return await self._set_crypto_order_terminal_state(order_id, "cancelled", webhook_payload)

    async def resolve_crypto_order_id(
        self,
        order_id: Optional[str] = None,
        provider_order_id: Optional[str] = None,
    ) -> Optional[str]:
        if order_id:
            return str(order_id)
        if provider_order_id:
            indexed = await self.redis.get_json(self._crypto_provider_order_key(str(provider_order_id)))
            if indexed:
                return indexed.get("order_id")
        return None

    async def _set_crypto_order_terminal_state(
        self,
        order_id: str,
        terminal_status: str,
        webhook_payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        order = await self.get_crypto_order(order_id)
        if not order:
            raise ValueError("Order not found")
        if order.get("status") == "paid":
            return {"order_id": order_id, "status": "paid", "already_processed": True}
        now = datetime.utcnow().isoformat()
        order["status"] = terminal_status
        order["updated_at"] = now
        order["webhook_payload"] = webhook_payload or order.get("webhook_payload")
        await self.redis.set_json(self._crypto_order_key(order_id), order, ex=CRYPTO_ORDER_TTL_SECONDS)
        return {"order_id": order_id, "status": terminal_status}

    async def _create_crypto_gateway_order(self, **payload: Any) -> dict[str, Any]:
        enabled = (
            await get_config_value("CRYPTO_PAYMENT_GATEWAY_ENABLED")
            or await get_config_value("USDT_PAYMENT_GATEWAY_ENABLED", "false")
            or "false"
        ).lower() == "true"
        base_url = (
            await get_config_value("CRYPTO_PAYMENT_GATEWAY_BASE_URL")
            or await get_config_value("USDT_PAYMENT_GATEWAY_BASE_URL")
        )
        api_key = (
            await get_config_value("CRYPTO_PAYMENT_GATEWAY_API_KEY")
            or await get_config_value("USDT_PAYMENT_GATEWAY_API_KEY")
        )
        create_path = await get_config_value("CRYPTO_PAYMENT_GATEWAY_CREATE_PATH", "/orders") or "/orders"

        if not enabled or not base_url or not api_key:
            return await self._create_local_crypto_order(
                order_id=str(payload["order_id"]),
                asset=str(payload["asset"]),
                network=str(payload["network"]),
                amount_crypto=round(int(payload["amount_usd_cents"]) / 100, 2),
                expires_at=datetime.utcnow() + timedelta(hours=24),
            )

        url = f"{base_url.rstrip('/')}/{create_path.lstrip('/')}"
        body = json.dumps(payload).encode("utf-8")

        def _request() -> dict[str, Any]:
            req = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "Idempotency-Key": str(payload["order_id"]),
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data) if data else {}

        try:
            result = await asyncio.to_thread(_request)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            logger.error(f"Crypto gateway order creation failed: HTTP {exc.code} - {error_body}")
            raise ValueError(f"Crypto gateway HTTP {exc.code}") from exc
        except Exception as exc:
            logger.error(f"Crypto gateway order creation failed: {exc}")
            raise ValueError("Crypto gateway request failed") from exc

        if not isinstance(result, dict):
            raise ValueError("Crypto gateway returned invalid response")
        return result

    async def _create_local_crypto_order(
        self,
        order_id: str,
        asset: str,
        network: str,
        amount_crypto: float,
        expires_at: datetime,
    ) -> dict[str, Any]:
        normalized_asset = asset.upper()
        normalized_network = network.upper()
        if normalized_network != "POLYGON":
            raise ValueError(f"Local crypto payment only supports POLYGON, got {normalized_network}")
        payment_address = await self._get_local_crypto_payment_address(
            order_id=order_id,
            asset=normalized_asset,
            network=normalized_network,
        )
        if not payment_address:
            raise ValueError(
                f"Local crypto payment address is not configured for {normalized_asset} {normalized_network}"
            )

        return {
            "provider_order_id": order_id,
            "status": "pending",
            "gateway": "local",
            "payment_address": payment_address,
            "payment_uri": self._build_crypto_payment_uri(
                asset=normalized_asset,
                network=normalized_network,
                address=payment_address,
                amount=amount_crypto,
            ),
            "expires_at": expires_at.isoformat(),
        }

    async def _get_local_crypto_payment_address(
        self,
        order_id: str,
        asset: str,
        network: str,
    ) -> Optional[str]:
        key_suffix = f"{asset}_{network}"
        pool_key = f"CRYPTO_PAYMENT_ADDRESS_POOL_{key_suffix}"
        pool_value = await get_config_value(pool_key) or self._get_backend_env_value(pool_key)
        if pool_value:
            addresses = [item.strip() for item in pool_value.split(",") if item.strip()]
            if addresses:
                index = uuid.UUID(order_id).int % len(addresses)
                return addresses[index]

        return (
            await get_config_value(f"CRYPTO_PAYMENT_ADDRESS_{key_suffix}")
            or self._get_backend_env_value(f"CRYPTO_PAYMENT_ADDRESS_{key_suffix}")
            or await get_config_value(f"CRYPTO_PAYMENT_FALLBACK_ADDRESS_{key_suffix}")
        )

    @staticmethod
    def _get_backend_env_value(key: str) -> Optional[str]:
        env_path = BACKEND_DIR / ".env"
        if not env_path.exists():
            return None
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                line_key, value = stripped.split("=", 1)
                if line_key.strip() == key:
                    return value.strip().strip('"').strip("'") or None
        except Exception as exc:
            logger.debug(f"Failed to read backend .env value for {key}: {exc}")
        return None

    @staticmethod
    def _build_crypto_payment_uri(asset: str, network: str, address: str, amount: float) -> str:
        amount_text = f"{float(amount):.6f}".rstrip("0").rstrip(".")
        query = f"asset={asset}&network={network}&amount={amount_text}"
        return f"ethereum:{address}?{query}"

    async def create_telegram_stars_order(
        self,
        user_id: str,
        amount_stars: int,
        credits: int,
        pack_id: Optional[str] = None,
        product_type: str = "credit_pack",
        tier: Optional[str] = None,
        billing_period: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict:
        normalized_product_type = (product_type or "credit_pack").lower()
        if normalized_product_type not in {"credit_pack", "subscription"}:
            raise ValueError("product_type must be credit_pack or subscription")

        order_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        order = {
            "order_id": order_id,
            "user_id": user_id,
            "amount_stars": int(amount_stars),
            "credits": int(credits),
            "pack_id": pack_id,
            "product_type": normalized_product_type,
            "tier": tier,
            "billing_period": billing_period,
            "title": title or f"{credits} Credits",
            "description": description or f"Top up {credits} credits",
            "metadata": metadata or {},
            "status": "pending",
            "created_at": now,
            "updated_at": now,
            "invoice_link": None,
            "charge_id": None,
            "paid_at": None,
            "failed_at": None,
            "cancelled_at": None,
            "webhook_payload": None,
            "credits_applied": False,
        }

        await self.redis.set_json(
            self._telegram_stars_order_key(order_id),
            order,
            ex=TELEGRAM_STARS_ORDER_TTL_SECONDS,
        )

        return {
            "order_id": order_id,
            "amount": int(amount_stars),
            "credits": credits,
            "product_type": normalized_product_type,
            "tier": tier,
            "billing_period": billing_period,
            "status": "pending",
            "raw": order,
        }

    async def get_telegram_stars_order(self, order_id: str) -> Optional[dict]:
        return await self.redis.get_json(self._telegram_stars_order_key(order_id))

    async def create_telegram_stars_invoice_link(
        self,
        order_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        order = await self.get_telegram_stars_order(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.get("status") != "pending":
            raise ValueError("Invoice can only be created for pending orders")

        bot_token = await get_config_value("TELEGRAM_BOT_TOKEN", self.settings.telegram_bot_token)
        if not bot_token:
            raise ValueError("Telegram bot token not configured")

        invoice_title = title or order.get("title") or f"{order.get('credits', 0)} Credits"
        invoice_description = description or order.get("description") or "Telegram Stars purchase"
        amount_stars = int(order.get("amount_stars", 0))
        if amount_stars <= 0:
            raise ValueError("Invalid Stars amount")

        payload = {
            "title": invoice_title,
            "description": invoice_description,
            "payload": f"stars:{order_id}",
            "currency": "XTR",
            "prices": [{"label": invoice_title, "amount": amount_stars}],
        }
        api_result = await self._telegram_api_post(bot_token, "createInvoiceLink", payload)
        invoice_link = api_result.get("result")
        if not invoice_link:
            raise ValueError("Telegram createInvoiceLink returned empty result")

        order["invoice_link"] = invoice_link
        order["updated_at"] = datetime.utcnow().isoformat()
        await self.redis.set_json(
            self._telegram_stars_order_key(order_id),
            order,
            ex=TELEGRAM_STARS_ORDER_TTL_SECONDS,
        )

        return {
            "order_id": order_id,
            "status": order["status"],
            "invoice_link": invoice_link,
            "raw": api_result,
        }

    async def answer_telegram_pre_checkout_query(
        self,
        pre_checkout_query_id: str,
        ok: bool,
        error_message: Optional[str] = None,
    ) -> dict[str, Any]:
        bot_token = await get_config_value("TELEGRAM_BOT_TOKEN", self.settings.telegram_bot_token)
        if not bot_token:
            raise ValueError("Telegram bot token not configured")

        payload: dict[str, Any] = {
            "pre_checkout_query_id": pre_checkout_query_id,
            "ok": ok,
        }
        if not ok and error_message:
            payload["error_message"] = error_message

        return await self._telegram_api_post(bot_token, "answerPreCheckoutQuery", payload)

    async def submit_telegram_stars_order(self, order_id: str, payment_id: str) -> dict:
        # Manual admin fallback. Uses the same paid flow as webhook to keep idempotency rules identical.
        return await self.mark_telegram_stars_order_paid(
            order_id=order_id,
            charge_id=payment_id,
            webhook_payload={"status": "paid", "order_id": order_id, "manual_submit": True},
        )

    async def _mark_cached_payment_order_paid(
        self,
        order: dict[str, Any],
        order_id: str,
        cache_key: str,
        gateway_label: str,
        charge_id: Optional[str] = None,
        webhook_payload: Optional[dict[str, Any]] = None,
    ) -> dict:
        from ..models.credit_transaction import CreditTransaction
        from ..models.user import User
        from .credit_service import credit_service

        current_status = order.get("status")
        if current_status in {"failed", "cancelled"}:
            raise ValueError(f"Cannot mark {current_status} order as paid")

        user_id = order.get("user_id")
        credits = int(order.get("credits", 0))
        if not user_id or credits <= 0:
            raise ValueError("Invalid order payload")

        product_type = str(order.get("product_type") or "credit_pack").lower()
        transaction_type = "subscription" if product_type == "subscription" else "purchase"
        credit_source = "monthly" if product_type == "subscription" else "purchased"
        already_paid = current_status == "paid"

        with self.db.transaction() as session:
            existing_tx = (
                session.query(CreditTransaction)
                .filter(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.order_id == order_id,
                    CreditTransaction.transaction_type == transaction_type,
                )
                .first()
            )

        credits_applied = existing_tx is not None
        if already_paid and bool(order.get("credits_applied")) and credits_applied:
            return {
                "order_id": order_id,
                "status": "paid",
                "already_processed": True,
                "credits_applied": True,
                "subscription_applied": bool(order.get("subscription_applied")),
            }

        if not credits_applied:
            await credit_service.add_credits(
                user_id=user_id,
                amount=credits,
                transaction_type=transaction_type,
                credit_source=credit_source,
                order_id=order_id,
                description=(
                    f"{gateway_label} subscription: {order.get('tier') or 'premium'} "
                    f"{order.get('billing_period') or ''}".strip()
                    if product_type == "subscription"
                    else f"Purchased {credits} credits via {gateway_label}"
                ),
            )
            credits_applied = True

        subscription_applied = bool(order.get("subscription_applied"))
        if product_type == "subscription":
            period = str(order.get("billing_period") or "1m").lower()
            period_days = {"1m": 30, "3m": 90, "12m": 365, "month": 30, "year": 365}.get(period, 30)
            with self.db.transaction() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    raise ValueError("User not found")
                now_dt = datetime.utcnow()
                current_end = user.subscription_end_date
                start = current_end if current_end and current_end > now_dt else now_dt
                user.tier = order.get("tier") or "premium"
                user.subscription_period = period
                user.subscription_start_date = user.subscription_start_date or now_dt
                user.subscription_end_date = start + timedelta(days=period_days)
                user.last_monthly_credit_grant = now_dt
                subscription_applied = True
            try:
                await self.redis.delete(f"user:balance:{user_id}")
            except Exception as exc:
                logger.debug(f"Failed to clear balance cache for {gateway_label} subscription {order_id}: {exc}")

        now = datetime.utcnow().isoformat()
        order["status"] = "paid"
        order["charge_id"] = charge_id or order.get("charge_id")
        order["paid_at"] = order.get("paid_at") or now
        order["updated_at"] = now
        order["credits_applied"] = credits_applied
        order["subscription_applied"] = subscription_applied
        order["webhook_payload"] = webhook_payload or order.get("webhook_payload")

        await self.redis.set_json(cache_key, order, ex=CRYPTO_ORDER_TTL_SECONDS)

        return {
            "order_id": order_id,
            "status": "paid",
            "already_processed": already_paid,
            "credits_applied": credits_applied,
            "subscription_applied": bool(order.get("subscription_applied")),
        }

    async def mark_telegram_stars_order_paid(
        self,
        order_id: str,
        charge_id: Optional[str] = None,
        webhook_payload: Optional[dict[str, Any]] = None,
    ) -> dict:
        order = await self.get_telegram_stars_order(order_id)
        if not order:
            raise ValueError("Order not found")

        return await self._mark_cached_payment_order_paid(
            order=order,
            order_id=order_id,
            cache_key=self._telegram_stars_order_key(order_id),
            gateway_label="Telegram Stars",
            charge_id=charge_id,
            webhook_payload=webhook_payload,
        )

    async def mark_telegram_stars_order_failed(
        self,
        order_id: str,
        webhook_payload: Optional[dict[str, Any]] = None,
    ) -> dict:
        return await self._set_telegram_stars_order_terminal_state(order_id, "failed", webhook_payload)

    async def mark_telegram_stars_order_cancelled(
        self,
        order_id: str,
        webhook_payload: Optional[dict[str, Any]] = None,
    ) -> dict:
        return await self._set_telegram_stars_order_terminal_state(order_id, "cancelled", webhook_payload)

    async def mark_telegram_stars_order_refunded(
        self,
        order_id: str,
        webhook_payload: Optional[dict[str, Any]] = None,
    ) -> dict:
        from ..models.credit_transaction import CreditTransaction
        from ..models.user import User

        order = await self.get_telegram_stars_order(order_id)
        if not order:
            raise ValueError("Order not found")

        user_id = order.get("user_id")
        if not user_id:
            raise ValueError("Order missing user_id")

        product_type = str(order.get("product_type") or "credit_pack").lower()
        purchase_type = "subscription" if product_type == "subscription" else "purchase"
        refund_source = "monthly" if product_type == "subscription" else "purchased"

        with self.db.transaction() as session:
            existing_refund = (
                session.query(CreditTransaction)
                .filter(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.order_id == order_id,
                    CreditTransaction.transaction_type == "refund_deduction",
                )
                .first()
            )
            if existing_refund:
                now = datetime.utcnow().isoformat()
                order["status"] = "refunded"
                order["updated_at"] = now
                order["refunded_at"] = now
                order["webhook_payload"] = webhook_payload or order.get("webhook_payload")
                await self.redis.set_json(
                    self._telegram_stars_order_key(order_id),
                    order,
                    ex=TELEGRAM_STARS_ORDER_TTL_SECONDS,
                )
                return {
                    "order_id": order_id,
                    "status": "refunded",
                    "already_processed": True,
                    "credits_deducted": 0.0,
                }

            purchase_tx = (
                session.query(CreditTransaction)
                .filter(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.order_id == order_id,
                    CreditTransaction.transaction_type == purchase_type,
                )
                .first()
            )
            if not purchase_tx:
                now = datetime.utcnow().isoformat()
                order["status"] = "refunded"
                order["updated_at"] = now
                order["refunded_at"] = now
                order["webhook_payload"] = webhook_payload or order.get("webhook_payload")
                await self.redis.set_json(
                    self._telegram_stars_order_key(order_id),
                    order,
                    ex=TELEGRAM_STARS_ORDER_TTL_SECONDS,
                )
                return {
                    "order_id": order_id,
                    "status": "refunded",
                    "already_processed": True,
                    "credits_deducted": 0.0,
                }

            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")

            available_bucket = user.monthly_credits if refund_source == "monthly" else user.purchased_credits
            credits_to_deduct = min(float(purchase_tx.amount or 0), float(available_bucket or 0))
            if refund_source == "monthly":
                user.monthly_credits = float(user.monthly_credits or 0) - credits_to_deduct
                if product_type == "subscription":
                    user.tier = "free"
                    user.subscription_end_date = None
                    user.subscription_period = None
            else:
                user.purchased_credits = float(user.purchased_credits or 0) - credits_to_deduct
            user.credits = float(user.monthly_credits or 0) + float(user.purchased_credits or 0)

            deduction_transaction = CreditTransaction(
                user_id=user.id,
                transaction_type="refund_deduction",
                amount=-credits_to_deduct,
                balance_after=user.credits,
                credit_source=refund_source,
                order_id=order_id,
                description=f"Telegram Stars {product_type} refund processed",
            )
            session.add(deduction_transaction)

        try:
            await self.redis.delete(f"user:balance:{user_id}")
        except Exception as exc:
            logger.debug(f"Failed to clear balance cache for Telegram Stars refund {order_id}: {exc}")

        now = datetime.utcnow().isoformat()
        order["status"] = "refunded"
        order["updated_at"] = now
        order["refunded_at"] = now
        order["webhook_payload"] = webhook_payload or order.get("webhook_payload")
        await self.redis.set_json(
            self._telegram_stars_order_key(order_id),
            order,
            ex=TELEGRAM_STARS_ORDER_TTL_SECONDS,
        )
        return {
            "order_id": order_id,
            "status": "refunded",
            "already_processed": False,
            "credits_deducted": credits_to_deduct,
        }

    async def _set_telegram_stars_order_terminal_state(
        self,
        order_id: str,
        terminal_status: str,
        webhook_payload: Optional[dict[str, Any]] = None,
    ) -> dict:
        order = await self.get_telegram_stars_order(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.get("status") == "paid":
            return {"order_id": order_id, "status": "paid", "already_processed": True}

        now = datetime.utcnow().isoformat()
        order["status"] = terminal_status
        order["updated_at"] = now
        if terminal_status == "failed":
            order["failed_at"] = now
        if terminal_status == "cancelled":
            order["cancelled_at"] = now
        order["webhook_payload"] = webhook_payload or order.get("webhook_payload")

        await self.redis.set_json(
            self._telegram_stars_order_key(order_id),
            order,
            ex=TELEGRAM_STARS_ORDER_TTL_SECONDS,
        )
        return {"order_id": order_id, "status": terminal_status}

    @staticmethod
    def _telegram_stars_order_key(order_id: str) -> str:
        return f"telegram_stars_order:{order_id}"

    @staticmethod
    def _crypto_order_key(order_id: str) -> str:
        return f"crypto_order:{order_id}"

    @staticmethod
    def _crypto_provider_order_key(provider_order_id: str) -> str:
        return f"crypto_provider_order:{provider_order_id}"

    @staticmethod
    def _crypto_order_response(order: dict[str, Any]) -> dict[str, Any]:
        return {
            "order_id": order.get("order_id"),
            "provider_order_id": order.get("provider_order_id"),
            "asset": order.get("asset"),
            "network": order.get("network"),
            "amount": order.get("amount_crypto"),
            "amount_crypto": order.get("amount_crypto"),
            "amount_usd_cents": order.get("amount_usd_cents"),
            "credits": order.get("credits"),
            "product_type": order.get("product_type"),
            "pack_id": order.get("pack_id"),
            "tier": order.get("tier"),
            "billing_period": order.get("billing_period"),
            "status": order.get("status"),
            "payment_address": order.get("payment_address"),
            "wallet_address": order.get("payment_address"),
            "payment_uri": order.get("payment_uri"),
            "checkout_url": order.get("checkout_url"),
            "expires_at": order.get("expires_at"),
            "created_at": order.get("created_at"),
            "updated_at": order.get("updated_at"),
            "raw": order,
        }

    async def _telegram_api_post(self, bot_token: str, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        api_url = f"https://api.telegram.org/bot{bot_token}/{method}"
        body = json.dumps(payload).encode("utf-8")

        def _request() -> dict[str, Any]:
            req = urllib.request.Request(
                api_url,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read().decode("utf-8")
                return json.loads(data)

        try:
            result = await asyncio.to_thread(_request)
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            logger.error(f"Telegram API error [{method}]: HTTP {exc.code} - {error_body}")
            raise ValueError(f"Telegram API HTTP {exc.code}") from exc
        except Exception as exc:
            logger.error(f"Telegram API request failed [{method}]: {exc}")
            raise ValueError("Telegram API request failed") from exc

        if not result.get("ok", False):
            logger.error(f"Telegram API returned failure [{method}]: {result}")
            raise ValueError(result.get("description") or "Telegram API returned failure")

        return result

    async def get_billing_history(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 20,
    ) -> dict[str, Any]:
        from ..models.credit_transaction import CreditTransaction

        with self.db.get_session() as session:
            query = session.query(CreditTransaction).filter(CreditTransaction.user_id == user_id)
            query = query.filter(
                CreditTransaction.transaction_type.in_(["purchase", "subscription", "refund_deduction"])
            )
            total = query.count()
            rows = (
                query.order_by(CreditTransaction.created_at.desc())
                .offset(max(0, offset))
                .limit(max(1, limit))
                .all()
            )

        payments: list[dict[str, Any]] = []
        for row in rows:
            tx_type = row.transaction_type or "purchase"
            if tx_type == "subscription":
                payment_type = "subscription"
            elif tx_type == "refund_deduction":
                payment_type = "refund"
            else:
                payment_type = "credit_pack"

            status = "refunded" if tx_type == "refund_deduction" else "succeeded"
            credits_granted = int(row.amount) if row.amount and row.amount > 0 else None

            payments.append(
                {
                    "id": str(row.id),
                    "type": payment_type,
                    "amount_cents": 0,
                    "currency": "USD",
                    "status": status,
                    "credits_granted": credits_granted,
                    "description": row.description or tx_type,
                    "created_at": row.created_at.isoformat() if row.created_at else datetime.utcnow().isoformat(),
                }
            )

        return {
            "payments": payments,
            "total": total,
            "limit": max(1, limit),
            "offset": max(0, offset),
        }

    async def create_credit_pack_checkout(
        self,
        user_id: str,
        pack_id: str,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> dict[str, Any]:
        from .pricing_service import pricing_service

        packs = await pricing_service.get_credit_packs(active_only=True)
        pack = next((p for p in packs if p.pack_id == pack_id), None)
        if not pack:
            raise ValueError("Invalid pack_id")

        credits = int((pack.credits or 0) + (pack.bonus_credits or 0))
        if credits <= 0:
            raise ValueError("Credit pack has invalid credits")

        checkout_success_url = success_url or "https://example.com/billing/success"
        checkout_cancel_url = cancel_url or "https://example.com/billing/cancel"

        stripe_key = await self._configure_stripe()
        if stripe_key:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": pack.name or f"{credits} Credits Pack",
                            },
                            "unit_amount": int(pack.price_cents),
                        },
                        "quantity": 1,
                    }
                ],
                mode="payment",
                success_url=checkout_success_url,
                cancel_url=checkout_cancel_url,
                metadata={
                    "user_id": user_id,
                    "pack_id": pack.pack_id,
                    "credits": credits,
                },
            )
            return {
                "checkout_url": session.url,
                "session_id": session.id,
                "pack_id": pack.pack_id,
                "credits": credits,
            }

        fallback_session_id = f"pack_{uuid.uuid4().hex[:12]}"
        return {
            "checkout_url": f"{checkout_success_url}?session_id={fallback_session_id}",
            "session_id": fallback_session_id,
            "pack_id": pack.pack_id,
            "credits": credits,
        }

    @staticmethod
    def _load_user_metadata(raw_metadata: Optional[str]) -> dict[str, Any]:
        if not raw_metadata:
            return {}
        try:
            parsed = json.loads(raw_metadata)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            logger.warning("Failed to parse user metadata JSON; falling back to empty dict")
        return {}

    @staticmethod
    def _extract_billing_state(metadata: dict[str, Any]) -> dict[str, Any]:
        billing_state = metadata.get("billing")
        if isinstance(billing_state, dict):
            return billing_state
        return {}

    async def get_current_subscription(self, user_id: str) -> dict[str, Any]:
        with self.db.get_session() as session:
            from ..models.user import User

            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "subscription": None,
                    "tier": "free",
                    "is_active": False,
                }

            now = datetime.utcnow()
            tier = (user.tier or "free").lower()
            current_period_end = user.subscription_end_date
            is_active = tier != "free" and (current_period_end is None or current_period_end > now)

            metadata = self._load_user_metadata(getattr(user, "user_metadata", None))
            billing_state = self._extract_billing_state(metadata)
            cancel_at_period_end = bool(billing_state.get("cancel_at_period_end", False))
            canceled_at = billing_state.get("cancel_at")

            subscription = None
            if tier != "free":
                period = "year" if (user.subscription_period or "").lower() == "1y" else "month"
                subscription = {
                    "id": f"sub_{user.id}",
                    "user_id": user.id,
                    "tier": tier,
                    "billing_period": period,
                    "status": "active" if is_active else "canceled",
                    "current_period_start": (
                        user.subscription_start_date.isoformat()
                        if user.subscription_start_date
                        else now.isoformat()
                    ),
                    "current_period_end": current_period_end.isoformat() if current_period_end else None,
                    "cancel_at_period_end": cancel_at_period_end,
                    "canceled_at": canceled_at if cancel_at_period_end else None,
                    "created_at": user.created_at.isoformat() if user.created_at else now.isoformat(),
                }

            return {
                "subscription": subscription,
                "tier": tier,
                "is_active": is_active,
            }

    async def create_subscription_checkout(
        self,
        user_id: str,
        tier: str,
        billing_period: str = "month",
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
    ) -> dict[str, Any]:
        normalized_tier = (tier or "").lower()
        if normalized_tier not in self.SUBSCRIPTION_TIERS:
            raise ValueError(f"Unsupported subscription tier: {tier}")

        normalized_period = (billing_period or "month").lower()
        if normalized_period not in {"month", "year"}:
            raise ValueError("billing_period must be 'month' or 'year'")

        checkout_success_url = success_url or "https://example.com/billing/success"
        checkout_cancel_url = cancel_url or "https://example.com/billing/cancel"

        session = await self.create_checkout_session(
            user_id=user_id,
            tier=normalized_tier,
            success_url=checkout_success_url,
            cancel_url=checkout_cancel_url,
            provider="stripe",
        )

        session["tier"] = normalized_tier
        session["billing_period"] = normalized_period
        return session

    async def get_subscription_portal_url(self, user_id: str, return_url: Optional[str] = None) -> str:
        fallback_url = return_url or "https://example.com/billing"

        with self.db.get_session() as session:
            from ..models.user import User

            user = session.query(User).filter(User.id == user_id).first()
            if not user or not user.stripe_customer_id:
                return fallback_url

            stripe_key = await self._configure_stripe()
            if not stripe_key:
                return fallback_url

            try:
                portal = stripe.billing_portal.Session.create(
                    customer=user.stripe_customer_id,
                    return_url=fallback_url,
                )
                return str(portal.url)
            except Exception as exc:
                logger.warning(f"Failed to create Stripe billing portal: {exc}")
                return fallback_url

    async def cancel_subscription(self, user_id: str) -> dict:
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.id == user_id).first()

            if not user or (user.tier or "free") == "free":
                return {"status": "no_active_subscription", "cancel_at": None}

            metadata = self._load_user_metadata(getattr(user, "user_metadata", None))
            billing_state = self._extract_billing_state(metadata)
            cancel_at = (user.subscription_end_date or datetime.utcnow()).isoformat()
            billing_state["cancel_at_period_end"] = True
            billing_state["cancel_at"] = cancel_at
            metadata["billing"] = billing_state
            user.user_metadata = json.dumps(metadata, ensure_ascii=False)
            session.commit()

            return {"status": "scheduled", "cancel_at": cancel_at}

    async def reactivate_subscription(self, user_id: str) -> dict:
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.id == user_id).first()

            if not user or (user.tier or "free") == "free":
                return {"status": "no_active_subscription"}

            metadata = self._load_user_metadata(getattr(user, "user_metadata", None))
            billing_state = self._extract_billing_state(metadata)
            billing_state["cancel_at_period_end"] = False
            billing_state.pop("cancel_at", None)
            metadata["billing"] = billing_state
            user.user_metadata = json.dumps(metadata, ensure_ascii=False)
            session.commit()

            return {"status": "reactivated"}

    async def health_check(self) -> dict:
        stripe_key = await get_config_value("STRIPE_SECRET_KEY", self.settings.stripe_secret_key)
        return {
            "status": "healthy",
            "stripe_enabled": bool(stripe_key),
        }
