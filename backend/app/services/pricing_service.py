import logging
import asyncio
from typing import Optional
from datetime import datetime
from functools import wraps
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..models.credit_config import CreditCostConfig
from ..models.credit_pack import CreditPack, DEFAULT_CREDIT_PACKS
from ..models.subscription_plan import SubscriptionPlan, DEFAULT_SUBSCRIPTION_PLANS
from ..services.database_service import DatabaseService
from ..schemas.credit import (
    CreditCostConfigResponse,
    CreditPackResponse,
    SubscriptionPlanResponse,
    BillingPricingConfigResponse,
)

logger = logging.getLogger(__name__)


def sync_to_async(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.get_event_loop().run_in_executor(None, lambda: func(*args, **kwargs))
    return wrapper


class PricingService:
    _instance = None
    _db: Optional[DatabaseService] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._db = DatabaseService()
        return cls._instance
    
    @property
    def db(self) -> DatabaseService:
        if self._db is None:
            self._db = DatabaseService()
        return self._db
    
    def _get_subscription_plans_sync(self, active_only: bool) -> list:
        with self.db.get_session() as session:
            query = session.query(SubscriptionPlan)
            if active_only:
                query = query.filter(SubscriptionPlan.is_active == True)
            return query.order_by(SubscriptionPlan.display_order).all()
    
    async def get_subscription_plans(self, active_only: bool = True) -> list:
        plans = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._get_subscription_plans_sync(active_only)
        )
        if not plans:
            await self._seed_subscription_plans()
            plans = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._get_subscription_plans_sync(active_only)
            )
        return plans
    
    def _get_subscription_plan_sync(self, period: str):
        with self.db.get_session() as session:
            return session.query(SubscriptionPlan).filter(
                SubscriptionPlan.period == period
            ).first()
    
    async def get_subscription_plan(self, period: str) -> Optional[SubscriptionPlan]:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._get_subscription_plan_sync(period)
        )
    
    def _update_subscription_plan_sync(self, period: str, **kwargs) -> dict:
        with self.db.transaction() as session:
            plan = session.query(SubscriptionPlan).filter(
                SubscriptionPlan.period == period
            ).first()
            
            if not plan:
                raise ValueError(f"Subscription plan {period} not found")
            
            for key, value in kwargs.items():
                if value is not None and hasattr(plan, key):
                    setattr(plan, key, value)
            
            plan.updated_at = datetime.utcnow()
            session.flush()
            session.refresh(plan)
            return self._plan_to_dict(plan)
    
    async def update_subscription_plan(
        self,
        period: str,
        price_cents: Optional[int] = None,
        monthly_equivalent_cents: Optional[int] = None,
        discount_percent: Optional[int] = None,
        is_active: Optional[bool] = None,
        display_order: Optional[int] = None,
    ) -> dict:
        kwargs = {
            "price_cents": price_cents,
            "monthly_equivalent_cents": monthly_equivalent_cents,
            "discount_percent": discount_percent,
            "is_active": is_active,
            "display_order": display_order,
        }
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._update_subscription_plan_sync(period, **kwargs)
            )
        except ValueError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error updating subscription plan: {e}")
            raise RuntimeError(f"Database error: {e}")
    
    def _get_credit_packs_sync(self, active_only: bool) -> list:
        with self.db.get_session() as session:
            query = session.query(CreditPack)
            if active_only:
                query = query.filter(CreditPack.is_active == True)
            return query.order_by(CreditPack.display_order).all()
    
    async def get_credit_packs(self, active_only: bool = True) -> list:
        packs = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._get_credit_packs_sync(active_only)
        )
        if not packs:
            await self._seed_credit_packs()
            packs = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._get_credit_packs_sync(active_only)
            )
        return packs
    
    def _get_credit_pack_sync(self, pack_id: str):
        with self.db.get_session() as session:
            return session.query(CreditPack).filter(
                CreditPack.pack_id == pack_id
            ).first()
    
    async def get_credit_pack(self, pack_id: str) -> Optional[CreditPack]:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._get_credit_pack_sync(pack_id)
        )
    
    def _create_credit_pack_sync(self, **kwargs) -> dict:
        with self.db.transaction() as session:
            existing = session.query(CreditPack).filter(
                CreditPack.pack_id == kwargs["pack_id"]
            ).first()
            if existing:
                raise ValueError(f"Credit pack {kwargs['pack_id']} already exists")
            
            pack = CreditPack(
                pack_id=kwargs["pack_id"],
                name=kwargs["name"],
                credits=kwargs["credits"],
                price_cents=kwargs["price_cents"],
                bonus_credits=kwargs.get("bonus_credits", 0),
                is_popular=kwargs.get("is_popular", False),
                display_order=kwargs.get("display_order", 0),
            )
            session.add(pack)
            session.flush()
            session.refresh(pack)
            return self._pack_to_dict(pack)
    
    async def create_credit_pack(
        self,
        pack_id: str,
        name: str,
        credits: int,
        price_cents: int,
        bonus_credits: int = 0,
        is_popular: bool = False,
        display_order: int = 0,
    ) -> dict:
        kwargs = {
            "pack_id": pack_id,
            "name": name,
            "credits": credits,
            "price_cents": price_cents,
            "bonus_credits": bonus_credits,
            "is_popular": is_popular,
            "display_order": display_order,
        }
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._create_credit_pack_sync(**kwargs)
            )
        except ValueError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error creating credit pack: {e}")
            raise RuntimeError(f"Database error: {e}")
    
    def _update_credit_pack_sync(self, pack_id: str, **kwargs) -> dict:
        with self.db.transaction() as session:
            pack = session.query(CreditPack).filter(
                CreditPack.pack_id == pack_id
            ).first()
            
            if not pack:
                raise ValueError(f"Credit pack {pack_id} not found")
            
            for key, value in kwargs.items():
                if value is not None and hasattr(pack, key):
                    setattr(pack, key, value)
            
            pack.updated_at = datetime.utcnow()
            session.flush()
            session.refresh(pack)
            return self._pack_to_dict(pack)
    
    async def update_credit_pack(
        self,
        pack_id: str,
        name: Optional[str] = None,
        credits: Optional[int] = None,
        price_cents: Optional[int] = None,
        bonus_credits: Optional[int] = None,
        is_popular: Optional[bool] = None,
        is_active: Optional[bool] = None,
        display_order: Optional[int] = None,
    ) -> dict:
        kwargs = {
            "name": name,
            "credits": credits,
            "price_cents": price_cents,
            "bonus_credits": bonus_credits,
            "is_popular": is_popular,
            "is_active": is_active,
            "display_order": display_order,
        }
        try:
            return await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._update_credit_pack_sync(pack_id, **kwargs)
            )
        except ValueError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error updating credit pack: {e}")
            raise RuntimeError(f"Database error: {e}")
    
    def _delete_credit_pack_sync(self, pack_id: str) -> bool:
        with self.db.transaction() as session:
            pack = session.query(CreditPack).filter(
                CreditPack.pack_id == pack_id
            ).first()
            
            if not pack:
                return False
            
            session.delete(pack)
            return True
    
    async def delete_credit_pack(self, pack_id: str) -> bool:
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._delete_credit_pack_sync(pack_id)
        )
    
    async def get_full_pricing_config(self) -> dict:
        def _get_config_sync():
            with self.db.get_session() as session:
                config = session.query(CreditCostConfig).first()
                if not config:
                    config = CreditCostConfig()
                    session.add(config)
                    session.commit()
                    session.refresh(config)
                return config
        
        config = await asyncio.get_event_loop().run_in_executor(None, _get_config_sync)
        plans = await self.get_subscription_plans(active_only=True)
        packs = await self.get_credit_packs(active_only=True)
        
        tier_benefits = {
            "free": {
                "monthly_credits": 0,
                "daily_checkin_credits": 0,
                "character_limit": 2,
                "message_cost": config.message_cost,
            },
            "premium": {
                "monthly_credits": config.premium_monthly_credits,
                "daily_checkin_credits": 0,
                "character_limit": 50,
                "message_cost": 0,
            },
        }
        
        return {
            "subscription_plans": [self._plan_to_dict(p) for p in plans],
            "credit_packs": [self._pack_to_dict(p) for p in packs],
            "credit_costs": {
                "message": config.message_cost,
                "voice": config.voice_cost,
                "image": config.image_cost,
                "video": config.video_cost,
                "voice_call_per_minute": config.voice_call_per_minute,
            },
            "tier_benefits": tier_benefits,
            "signup_bonus_credits": config.signup_bonus_credits,
        }
    
    def _plan_to_dict(self, plan) -> dict:
        return {
            "period": plan.period,
            "price_cents": plan.price_cents,
            "monthly_equivalent_cents": plan.monthly_equivalent_cents,
            "discount_percent": plan.discount_percent,
            "is_active": plan.is_active,
            "display_order": plan.display_order,
        }
    
    def _pack_to_dict(self, pack) -> dict:
        return {
            "id": pack.pack_id,
            "name": pack.name,
            "credits": pack.credits,
            "price_cents": pack.price_cents,
            "bonus_credits": pack.bonus_credits,
            "total_credits": pack.credits + (pack.bonus_credits or 0),
            "is_popular": pack.is_popular,
            "is_active": pack.is_active,
            "display_order": pack.display_order,
        }
    
    def _seed_subscription_plans_sync(self):
        with self.db.transaction() as session:
            for plan_data in DEFAULT_SUBSCRIPTION_PLANS:
                existing = session.query(SubscriptionPlan).filter(
                    SubscriptionPlan.period == plan_data["period"]
                ).first()
                if not existing:
                    plan = SubscriptionPlan(**plan_data)
                    session.add(plan)
            logger.info("Seeded default subscription plans")
    
    async def _seed_subscription_plans(self):
        await asyncio.get_event_loop().run_in_executor(
            None, self._seed_subscription_plans_sync
        )
    
    def _seed_credit_packs_sync(self):
        with self.db.transaction() as session:
            for pack_data in DEFAULT_CREDIT_PACKS:
                existing = session.query(CreditPack).filter(
                    CreditPack.pack_id == pack_data["pack_id"]
                ).first()
                if not existing:
                    pack = CreditPack(**pack_data)
                    session.add(pack)
            logger.info("Seeded default credit packs")
    
    async def _seed_credit_packs(self):
        await asyncio.get_event_loop().run_in_executor(
            None, self._seed_credit_packs_sync
        )
    
    async def initialize_default_data(self):
        await self._seed_subscription_plans()
        await self._seed_credit_packs()
        
        def _init_config_sync():
            with self.db.transaction() as session:
                config = session.query(CreditCostConfig).first()
                if not config:
                    config = CreditCostConfig()
                    session.add(config)
                    logger.info("Initialized default credit cost config")
        
        await asyncio.get_event_loop().run_in_executor(None, _init_config_sync)


pricing_service = PricingService()
