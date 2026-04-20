from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    PAST_DUE = "past_due"


class PaymentProvider(str, Enum):
    STRIPE = "stripe"
    CCBILL = "ccbill"
    USDT = "usdt"
    TELEGRAM_STARS = "telegram_stars"


class Subscription(BaseModel):
    id: str
    user_id: str
    provider: PaymentProvider
    provider_subscription_id: Optional[str] = None
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    tier: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreditPack(BaseModel):
    id: str
    name: str
    credits: int
    price: float
    currency: str = "USD"
    bonus: int = 0
    popular: bool = False


class CheckoutRequest(BaseModel):
    pack_id: Optional[str] = None
    tier: Optional[str] = None
    success_url: str
    cancel_url: str
    provider: PaymentProvider = PaymentProvider.STRIPE


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


class CreditBalance(BaseModel):
    credits: int
    subscription_tier: Optional[str] = None
    subscription_end: Optional[datetime] = None


class BillingHistory(BaseModel):
    id: str
    user_id: str
    amount: float
    currency: str
    description: str
    status: str
    created_at: datetime


class USDTOrder(BaseModel):
    id: str
    user_id: str
    amount: float
    credits: int
    wallet_address: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None


class WebhookEvent(BaseModel):
    provider: PaymentProvider
    event_type: str
    data: dict[str, Any]
    signature: Optional[str] = None
