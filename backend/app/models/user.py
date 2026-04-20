from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(128), primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(100), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    
    tier = Column(String(20), default="free")
    
    user_type = Column(String(20), default="free")
    subscription_period = Column(String(10), nullable=True)
    subscription_start_date = Column(DateTime, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)
    stripe_customer_id = Column(String(128), nullable=True, index=True)
    
    credits = Column(Float, default=0.0)
    purchased_credits = Column(Float, default=0.0)
    monthly_credits = Column(Float, default=0.0)
    total_credits_earned = Column(Float, default=0.0)
    total_credits_spent = Column(Float, default=0.0)
    last_monthly_credit_grant = Column(DateTime, nullable=True)
    signup_bonus_granted = Column(Boolean, default=False)
    
    user_metadata = Column("metadata", Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def subscription_tier(self):
        return self.tier
    
    @subscription_tier.setter
    def subscription_tier(self, value):
        self.tier = value


class UserCreate(BaseModel):
    email: EmailStr
    display_name: Optional[str] = None


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPreferences(BaseModel):
    voice_presence: Optional[str] = "auto"
    content_preferences: Optional[dict] = None


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    tier: str
    credits: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreditBalance(BaseModel):
    credits: float
    tier: str
    next_refill_hours: Optional[int] = None