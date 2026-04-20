import logging
import stripe
from datetime import datetime, timedelta
from typing import Optional
import uuid
import json

from ..core.config import get_settings, get_config_value
from .redis_service import RedisService
from .database_service import DatabaseService

logger = logging.getLogger(__name__)


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

    async def create_usdt_order(
        self,
        user_id: str,
        amount: float,
        credits: int,
    ) -> dict:
        order_id = str(uuid.uuid4())
        
        wallet_address = "TExampleWalletAddress123"
        
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        await self.redis.set(
            f"usdt_order:{order_id}",
            {
                "user_id": user_id,
                "amount": amount,
                "credits": credits,
                "wallet_address": wallet_address,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat(),
            },
            ex=86400,
        )
        
        return {
            "order_id": order_id,
            "amount": amount,
            "credits": credits,
            "wallet_address": wallet_address,
            "expires_at": expires_at.isoformat(),
        }

    async def get_usdt_order(self, order_id: str) -> Optional[dict]:
        return await self.redis.get(f"usdt_order:{order_id}")

    async def submit_usdt_order(self, order_id: str, tx_hash: str) -> dict:
        order = await self.redis.get(f"usdt_order:{order_id}")
        
        if not order:
            raise ValueError("Order not found")
        
        if order.get("status") != "pending":
            raise ValueError("Order already processed")
        
        order["status"] = "processing"
        order["tx_hash"] = tx_hash
        
        await self.redis.set(f"usdt_order:{order_id}", order, ex=86400 * 7)
        
        return {"order_id": order_id, "status": "processing"}

    async def create_telegram_stars_order(
        self,
        user_id: str,
        amount: int,
        credits: int,
    ) -> dict:
        order_id = str(uuid.uuid4())
        
        await self.redis.set(
            f"telegram_stars_order:{order_id}",
            {
                "user_id": user_id,
                "amount": amount,
                "credits": credits,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            },
            ex=86400,
        )
        
        return {
            "order_id": order_id,
            "amount": amount,
            "credits": credits,
        }

    async def get_telegram_stars_order(self, order_id: str) -> Optional[dict]:
        return await self.redis.get(f"telegram_stars_order:{order_id}")

    async def submit_telegram_stars_order(self, order_id: str, payment_id: str) -> dict:
        order = await self.redis.get(f"telegram_stars_order:{order_id}")
        
        if not order:
            raise ValueError("Order not found")
        
        order["status"] = "completed"
        order["payment_id"] = payment_id
        
        user_id = order.get("user_id")
        credits = order.get("credits", 0)
        
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.firebase_uid == user_id).first()
            
            if user:
                user.credits += credits
                session.commit()
        
        await self.redis.delete(f"telegram_stars_order:{order_id}")
        
        return {"order_id": order_id, "status": "completed"}

    async def get_billing_history(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[dict]:
        return []

    async def cancel_subscription(self, user_id: str) -> dict:
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.firebase_uid == user_id).first()
            
            if user:
                user.subscription_tier = "free"
                session.commit()
        
        return {"status": "cancelled"}

    async def reactivate_subscription(self, user_id: str) -> dict:
        return {"status": "reactivated"}

    async def health_check(self) -> dict:
        stripe_key = await get_config_value("STRIPE_SECRET_KEY", self.settings.stripe_secret_key)
        return {
            "status": "healthy",
            "stripe_enabled": bool(stripe_key),
        }