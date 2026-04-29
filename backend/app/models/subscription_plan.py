from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(10), unique=True, nullable=False, comment="周期: 1m, 3m, 12m")
    price_cents = Column(Integer, nullable=False, comment="总价(分)")
    monthly_equivalent_cents = Column(Integer, nullable=False, comment="月均价格(分)")
    discount_percent = Column(Integer, default=0, comment="折扣百分比")
    is_active = Column(Boolean, default=True, comment="是否启用")
    display_order = Column(Integer, default=0, comment="显示顺序")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "period": self.period,
            "price_cents": self.price_cents,
            "monthly_equivalent_cents": self.monthly_equivalent_cents,
            "discount_percent": self.discount_percent,
            "is_active": self.is_active,
            "display_order": self.display_order,
        }


DEFAULT_SUBSCRIPTION_PLANS = [
    {"period": "1m", "price_cents": 1399, "monthly_equivalent_cents": 1399, "discount_percent": 0, "display_order": 1},
    {"period": "3m", "price_cents": 2697, "monthly_equivalent_cents": 899, "discount_percent": 35, "display_order": 2},
    {"period": "12m", "price_cents": 4788, "monthly_equivalent_cents": 399, "discount_percent": 70, "display_order": 3},
]
