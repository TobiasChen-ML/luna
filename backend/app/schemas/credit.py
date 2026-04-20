from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CreditCostConfigResponse(BaseModel):
    message_cost: float = Field(default=0.1, description="文本消息消耗")
    voice_cost: float = Field(default=0.2, description="语音生成消耗")
    image_cost: int = Field(default=2, description="图片生成消耗")
    video_cost: int = Field(default=4, description="视频生成消耗")
    voice_call_per_minute: int = Field(default=3, description="实时通话每分钟消耗")
    signup_bonus_credits: int = Field(default=10, description="注册奖励credits")
    premium_monthly_credits: int = Field(default=100, description="订阅用户每月credits")


class CreditCostConfigUpdate(BaseModel):
    message_cost: Optional[float] = None
    voice_cost: Optional[float] = None
    image_cost: Optional[int] = None
    video_cost: Optional[int] = None
    voice_call_per_minute: Optional[int] = None
    signup_bonus_credits: Optional[int] = None
    premium_monthly_credits: Optional[int] = None


class CreditPackResponse(BaseModel):
    id: str
    name: str
    credits: int
    price_cents: int
    bonus_credits: int = 0
    total_credits: int
    is_popular: bool = False
    is_active: bool = True
    display_order: int = 0


class CreditPackCreate(BaseModel):
    pack_id: str
    name: str
    credits: int
    price_cents: int
    bonus_credits: int = 0
    is_popular: bool = False
    display_order: int = 0


class CreditPackUpdate(BaseModel):
    name: Optional[str] = None
    credits: Optional[int] = None
    price_cents: Optional[int] = None
    bonus_credits: Optional[int] = None
    is_popular: Optional[bool] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class SubscriptionPlanResponse(BaseModel):
    period: str
    price_cents: int
    monthly_equivalent_cents: int
    discount_percent: int = 0
    is_active: bool = True
    display_order: int = 0


class SubscriptionPlanUpdate(BaseModel):
    price_cents: Optional[int] = None
    monthly_equivalent_cents: Optional[int] = None
    discount_percent: Optional[int] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class CreditBalanceResponse(BaseModel):
    total: float = Field(description="总余额")
    purchased: float = Field(description="购买的credits")
    monthly: float = Field(description="订阅的credits")
    subscription_tier: str = Field(default="free")
    subscription_period: Optional[str] = None
    subscription_end: Optional[datetime] = None
    signup_bonus_granted: bool = False


class DeductCreditsRequest(BaseModel):
    amount: float = Field(description="扣费数量")
    usage_type: str = Field(description="message, voice, image, video, voice_call")
    character_id: Optional[str] = None
    session_id: Optional[str] = None
    order_id: Optional[str] = None


class AddCreditsRequest(BaseModel):
    amount: float = Field(description="增加数量")
    transaction_type: str = Field(description="signup_bonus, subscription, purchase, refund, admin_adjust")
    credit_source: Optional[str] = Field(default="purchased", description="purchased or monthly")
    order_id: Optional[str] = None
    description: Optional[str] = None


class CreditTransactionResponse(BaseModel):
    id: int
    transaction_type: str
    amount: float
    balance_after: float
    usage_type: Optional[str] = None
    credit_source: Optional[str] = None
    order_id: Optional[str] = None
    character_id: Optional[str] = None
    session_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


class AdminAdjustCreditsRequest(BaseModel):
    user_id: str
    amount: float = Field(description="调整数量，正数增加，负数减少")
    description: str = Field(description="调整原因")


class BillingPricingConfigResponse(BaseModel):
    subscription_plans: list[SubscriptionPlanResponse]
    credit_packs: list[CreditPackResponse]
    credit_costs: CreditCostConfigResponse
    tier_benefits: dict