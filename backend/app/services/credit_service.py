import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from ..models.user import User
from ..models.credit_config import CreditCostConfig
from ..models.credit_transaction import CreditTransaction
from ..models.credit_pack import CreditPack, DEFAULT_CREDIT_PACKS
from ..models.subscription_plan import SubscriptionPlan, DEFAULT_SUBSCRIPTION_PLANS
from ..services.database_service import DatabaseService
from ..services.redis_service import RedisService

logger = logging.getLogger(__name__)


BALANCE_CACHE_PREFIX = "user:balance:"
BALANCE_CACHE_TTL = 3600


class InsufficientCreditsError(Exception):
    pass


class CreditService:
    def __init__(
        self,
        db: Optional[DatabaseService] = None,
        redis: Optional[RedisService] = None,
    ):
        self.db = db or DatabaseService()
        self.redis = redis or RedisService()
    
    def _get_session(self) -> Session:
        return self.db.get_session()
    
    def _get_balance_cache_key(self, user_id: str) -> str:
        return f"{BALANCE_CACHE_PREFIX}{user_id}"
    
    async def _get_cached_balance(self, user_id: str) -> Optional[dict]:
        try:
            cached = await self.redis.get_json(self._get_balance_cache_key(user_id))
            if cached:
                if cached.get("subscription_end"):
                    cached["subscription_end"] = datetime.fromisoformat(cached["subscription_end"])
            return cached
        except Exception:
            return None
    
    async def _update_balance_cache(self, user_id: str, balance: dict) -> None:
        try:
            cache_data = balance.copy()
            if cache_data.get("subscription_end"):
                cache_data["subscription_end"] = cache_data["subscription_end"].isoformat() if isinstance(cache_data["subscription_end"], datetime) else cache_data["subscription_end"]
            await self.redis.set_json(
                self._get_balance_cache_key(user_id),
                cache_data,
                ex=BALANCE_CACHE_TTL
            )
        except Exception as e:
            logger.debug(f"Failed to update balance cache for user {user_id}: {e}")
    
    async def get_config(self) -> dict:
        with self.db.transaction() as session:
            config = session.query(CreditCostConfig).first()
            if not config:
                config = CreditCostConfig()
                session.add(config)
                session.flush()
            return {
                "message_cost": float(config.message_cost or 0.1),
                "voice_cost": float(config.voice_cost or 0.2),
                "image_cost": int(config.image_cost or 2),
                "video_cost": int(config.video_cost or 4),
                "voice_call_per_minute": int(config.voice_call_per_minute or 3),
                "signup_bonus_credits": int(config.signup_bonus_credits or 10),
                "premium_monthly_credits": int(config.premium_monthly_credits or 100),
            }
    
    async def update_config(self, data: dict, admin_email: str) -> dict:
        with self.db.transaction() as session:
            config = session.query(CreditCostConfig).first()
            if not config:
                config = CreditCostConfig()
                session.add(config)
            
            for key, value in data.items():
                if value is not None and hasattr(config, key):
                    setattr(config, key, value)
            
            config.updated_by = admin_email
            config.updated_at = datetime.utcnow()
            session.flush()
            
            return {
                "message_cost": float(config.message_cost or 0.1),
                "voice_cost": float(config.voice_cost or 0.2),
                "image_cost": int(config.image_cost or 2),
                "video_cost": int(config.video_cost or 4),
                "voice_call_per_minute": int(config.voice_call_per_minute or 3),
                "signup_bonus_credits": int(config.signup_bonus_credits or 10),
                "premium_monthly_credits": int(config.premium_monthly_credits or 100),
                "updated_by": config.updated_by,
                "updated_at": config.updated_at.isoformat() if config.updated_at else None,
            }
    
    async def get_balance(self, user_id: str) -> dict:
        cached = await self._get_cached_balance(user_id)
        if cached:
            return cached
        
        balance = await self._get_balance_from_db(user_id)
        
        await self._update_balance_cache(user_id, balance)
        
        return balance
    
    async def _get_balance_from_db(self, user_id: str) -> dict:
        with self.db.transaction() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "total": 0.0,
                    "purchased": 0.0,
                    "monthly": 0.0,
                    "subscription_tier": "free",
                    "subscription_period": None,
                    "subscription_end": None,
                    "signup_bonus_granted": False,
                }
            
            return {
                "total": float(user.credits or 0),
                "purchased": float(user.purchased_credits or 0),
                "monthly": float(user.monthly_credits or 0),
                "subscription_tier": user.tier or "free",
                "subscription_period": user.subscription_period,
                "subscription_end": user.subscription_end_date,
                "signup_bonus_granted": user.signup_bonus_granted or False,
            }
    
    async def deduct_credits(
        self,
        user_id: str,
        amount: float,
        usage_type: str,
        character_id: Optional[str] = None,
        session_id: Optional[str] = None,
        order_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        with self.db.transaction() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            total_credits = float(user.credits or 0)
            if total_credits < amount:
                raise InsufficientCreditsError(
                    f"Insufficient credits: has {total_credits}, needs {amount}"
                )
            
            monthly_credits = float(user.monthly_credits or 0)
            purchased_credits = float(user.purchased_credits or 0)
            
            credit_source = None
            remaining_to_deduct = amount
            
            if monthly_credits >= remaining_to_deduct:
                user.monthly_credits = monthly_credits - remaining_to_deduct
                credit_source = "monthly"
                remaining_to_deduct = 0
            else:
                if monthly_credits > 0:
                    remaining_to_deduct -= monthly_credits
                    user.monthly_credits = 0
                    credit_source = "monthly"
                
                if remaining_to_deduct > 0:
                    if purchased_credits < remaining_to_deduct:
                        raise InsufficientCreditsError(
                            f"Insufficient purchased credits: has {purchased_credits}, needs {remaining_to_deduct}"
                        )
                    user.purchased_credits = purchased_credits - remaining_to_deduct
                    credit_source = "purchased" if credit_source is None else "mixed"
                    remaining_to_deduct = 0
            
            user.credits = float(user.monthly_credits or 0) + float(user.purchased_credits or 0)
            user.total_credits_spent = float(user.total_credits_spent or 0) + amount
            
            transaction = CreditTransaction(
                user_id=user.id,
                transaction_type="usage",
                amount=-amount,
                balance_after=user.credits,
                usage_type=usage_type,
                credit_source=credit_source,
                character_id=character_id,
                session_id=session_id,
                order_id=order_id,
                description=description or f"Used {amount} credits for {usage_type}",
            )
            session.add(transaction)
            session.flush()
            
            new_balance = {
                "total": float(user.credits),
                "purchased": float(user.purchased_credits or 0),
                "monthly": float(user.monthly_credits or 0),
                "subscription_tier": user.tier or "free",
                "subscription_period": user.subscription_period,
                "subscription_end": user.subscription_end_date,
                "signup_bonus_granted": user.signup_bonus_granted or False,
            }
        
        await self._update_balance_cache(user_id, new_balance)
        logger.info(f"Deducted {amount} credits from user {user_id} for {usage_type}")
        return True
    
    async def add_credits(
        self,
        user_id: str,
        amount: float,
        transaction_type: str,
        credit_source: str = "purchased",
        order_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        with self.db.transaction() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            if credit_source == "purchased":
                user.purchased_credits = float(user.purchased_credits or 0) + amount
            elif credit_source == "monthly":
                user.monthly_credits = float(user.monthly_credits or 0) + amount
            else:
                user.purchased_credits = float(user.purchased_credits or 0) + amount
            
            user.credits = float(user.monthly_credits or 0) + float(user.purchased_credits or 0)
            user.total_credits_earned = float(user.total_credits_earned or 0) + amount
            
            transaction = CreditTransaction(
                user_id=user.id,
                transaction_type=transaction_type,
                amount=amount,
                balance_after=user.credits,
                credit_source=credit_source,
                order_id=order_id,
                description=description or f"Added {amount} credits ({transaction_type})",
            )
            session.add(transaction)
            session.flush()
            
            new_balance = {
                "total": float(user.credits),
                "purchased": float(user.purchased_credits or 0),
                "monthly": float(user.monthly_credits or 0),
                "subscription_tier": user.tier or "free",
                "subscription_period": user.subscription_period,
                "subscription_end": user.subscription_end_date,
                "signup_bonus_granted": user.signup_bonus_granted or False,
            }
        
        await self._update_balance_cache(user_id, new_balance)
        logger.info(f"Added {amount} credits to user {user_id} ({transaction_type})")
        return True
    
    async def grant_signup_bonus(self, user_id: str) -> bool:
        config = await self.get_config()
        bonus_amount = float(config['signup_bonus_credits'] or 10)

        with self.db.transaction() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")

            if user.signup_bonus_granted:
                logger.info(f"User {user_id} already received signup bonus")
                return False
            
            user.purchased_credits = float(user.purchased_credits or 0) + bonus_amount
            user.credits = float(user.monthly_credits or 0) + float(user.purchased_credits or 0)
            user.total_credits_earned = float(user.total_credits_earned or 0) + bonus_amount
            user.signup_bonus_granted = True
            user.user_type = "free"
            
            transaction = CreditTransaction(
                user_id=user.id,
                transaction_type="signup_bonus",
                amount=bonus_amount,
                balance_after=user.credits,
                credit_source="purchased",
                description=f"Signup bonus: {bonus_amount} credits",
            )
            session.add(transaction)
            session.flush()
            
            new_balance = {
                "total": float(user.credits),
                "purchased": float(user.purchased_credits or 0),
                "monthly": float(user.monthly_credits or 0),
                "subscription_tier": user.tier or "free",
                "subscription_period": user.subscription_period,
                "subscription_end": user.subscription_end_date,
                "signup_bonus_granted": True,
            }
        
        await self._update_balance_cache(user_id, new_balance)
        logger.info(f"Granted signup bonus of {bonus_amount} credits to user {user_id}")
        return True
    
    async def grant_monthly_credits(self, user_id: str) -> bool:
        with self.db.transaction() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            if user.subscription_tier == "free" or not user.subscription_end_date:
                logger.info(f"User {user_id} is not a subscriber, skipping monthly credits")
                return False
            
            if user.last_monthly_credit_grant:
                last_grant = user.last_monthly_credit_grant
                if datetime.utcnow() - last_grant < timedelta(days=28):
                    logger.info(f"User {user_id} already received monthly credits recently")
                    return False
            
            config = await self.get_config()
            monthly_amount = float(config['premium_monthly_credits'] or 100)
            
            user.monthly_credits = float(user.monthly_credits or 0) + monthly_amount
            user.credits = float(user.monthly_credits or 0) + float(user.purchased_credits or 0)
            user.total_credits_earned = float(user.total_credits_earned or 0) + monthly_amount
            user.last_monthly_credit_grant = datetime.utcnow()
            
            transaction = CreditTransaction(
                user_id=user.id,
                transaction_type="subscription",
                amount=monthly_amount,
                balance_after=user.credits,
                credit_source="monthly",
                description=f"Monthly subscription credits: {monthly_amount}",
            )
            session.add(transaction)
            session.flush()
            
            new_balance = {
                "total": float(user.credits),
                "purchased": float(user.purchased_credits or 0),
                "monthly": float(user.monthly_credits or 0),
                "subscription_tier": user.tier or "free",
                "subscription_period": user.subscription_period,
                "subscription_end": user.subscription_end_date,
                "signup_bonus_granted": user.signup_bonus_granted or False,
            }
        
        await self._update_balance_cache(user_id, new_balance)
        logger.info(f"Granted {monthly_amount} monthly credits to user {user_id}")
        return True
    
    async def check_and_grant_monthly_credits(self, user_id: str) -> bool:
        return await self.grant_monthly_credits(user_id)
    
    async def get_transactions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[CreditTransaction]:
        with self.db.get_session() as session:
            transactions = (
                session.query(CreditTransaction)
                .filter(CreditTransaction.user_id == user_id)
                .order_by(CreditTransaction.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return transactions
    
    async def get_all_transactions(
        self,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None,
        transaction_type: Optional[str] = None,
    ) -> tuple[list[CreditTransaction], int]:
        with self.db.get_session() as session:
            query = session.query(CreditTransaction)
            
            if user_id:
                query = query.filter(CreditTransaction.user_id == user_id)
            if transaction_type:
                query = query.filter(CreditTransaction.transaction_type == transaction_type)
            
            total = query.count()
            transactions = (
                query
                .order_by(CreditTransaction.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return transactions, total
    
    async def admin_adjust_credits(
        self,
        user_id: str,
        amount: float,
        description: str,
        admin_email: str,
    ) -> bool:
        with self.db.transaction() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            if amount >= 0:
                user.purchased_credits = float(user.purchased_credits or 0) + amount
                user.total_credits_earned = float(user.total_credits_earned or 0) + amount
            else:
                if user.credits < abs(amount):
                    raise InsufficientCreditsError(
                        f"Cannot deduct {abs(amount)} credits, user only has {user.credits}"
                    )
                total_to_deduct = abs(amount)
                monthly_credits = float(user.monthly_credits or 0)
                purchased_credits = float(user.purchased_credits or 0)
                
                if monthly_credits >= total_to_deduct:
                    user.monthly_credits = monthly_credits - total_to_deduct
                else:
                    remaining = total_to_deduct - monthly_credits
                    user.monthly_credits = 0
                    user.purchased_credits = max(0, purchased_credits - remaining)
                
                user.total_credits_spent = float(user.total_credits_spent or 0) + abs(amount)
            
            user.credits = float(user.monthly_credits or 0) + float(user.purchased_credits or 0)
            
            transaction = CreditTransaction(
                user_id=user.id,
                transaction_type="admin_adjust",
                amount=amount,
                balance_after=user.credits,
                credit_source="purchased",
                description=f"Admin adjustment by {admin_email}: {description}",
            )
            session.add(transaction)
            session.flush()
            
            new_balance = {
                "total": float(user.credits),
                "purchased": float(user.purchased_credits or 0),
                "monthly": float(user.monthly_credits or 0),
                "subscription_tier": user.tier or "free",
                "subscription_period": user.subscription_period,
                "subscription_end": user.subscription_end_date,
                "signup_bonus_granted": user.signup_bonus_granted or False,
            }
        
        await self._update_balance_cache(user_id, new_balance)
        logger.info(f"Admin {admin_email} adjusted {amount} credits for user {user_id}")
        return True


    async def refund_credits(
        self,
        user_id: str,
        amount: float,
        original_transaction_id: str,
        reason: str,
    ) -> bool:
        with self.db.transaction() as session:
            existing_refund = session.query(CreditTransaction).filter(
                CreditTransaction.user_id == user_id,
                CreditTransaction.transaction_type == "refund",
                CreditTransaction.description.contains(original_transaction_id)
            ).first()
            
            if existing_refund:
                logger.warning(f"Duplicate refund attempt for transaction {original_transaction_id}")
                raise ValueError(f"Already refunded for transaction {original_transaction_id}")
            
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            user.purchased_credits = float(user.purchased_credits or 0) + amount
            user.credits = float(user.monthly_credits or 0) + float(user.purchased_credits or 0)
            user.total_credits_earned = float(user.total_credits_earned or 0) + amount
            
            transaction = CreditTransaction(
                user_id=user.id,
                transaction_type="refund",
                amount=amount,
                balance_after=user.credits,
                credit_source="purchased",
                description=f"Refund: {reason} (original_tx: {original_transaction_id})",
            )
            session.add(transaction)
            session.flush()
            
            new_balance = {
                "total": float(user.credits),
                "purchased": float(user.purchased_credits or 0),
                "monthly": float(user.monthly_credits or 0),
                "subscription_tier": user.tier or "free",
                "subscription_period": user.subscription_period,
                "subscription_end": user.subscription_end_date,
                "signup_bonus_granted": user.signup_bonus_granted or False,
            }
        
        await self._update_balance_cache(user_id, new_balance)
        logger.info(f"Refunded {amount} credits to user {user_id} for transaction {original_transaction_id}")
        return True
    
    async def refund_credits_simple(
        self,
        user_id: str,
        amount: float,
        usage_type: str,
        character_id: Optional[str] = None,
        session_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
        with self.db.transaction() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            user.purchased_credits = float(user.purchased_credits or 0) + amount
            user.credits = float(user.monthly_credits or 0) + float(user.purchased_credits or 0)
            user.total_credits_earned = float(user.total_credits_earned or 0) + amount
            
            transaction = CreditTransaction(
                user_id=user.id,
                transaction_type="refund",
                amount=amount,
                balance_after=user.credits,
                credit_source="purchased",
                usage_type=usage_type,
                character_id=character_id,
                session_id=session_id,
                description=description or f"Refund for failed {usage_type}",
            )
            session.add(transaction)
            session.flush()
            
            new_balance = {
                "total": float(user.credits),
                "purchased": float(user.purchased_credits or 0),
                "monthly": float(user.monthly_credits or 0),
                "subscription_tier": user.tier or "free",
                "subscription_period": user.subscription_period,
                "subscription_end": user.subscription_end_date,
                "signup_bonus_granted": user.signup_bonus_granted or False,
            }
        
        await self._update_balance_cache(user_id, new_balance)
        logger.info(f"Refunded {amount} credits to user {user_id} for {usage_type}")
        return True


credit_service = CreditService()
