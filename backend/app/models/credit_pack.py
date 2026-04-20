from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CreditPack(Base):
    __tablename__ = "credit_packs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pack_id = Column(String(50), unique=True, nullable=False, comment="充值包ID")
    name = Column(String(100), nullable=False, comment="显示名称")
    credits = Column(Integer, nullable=False, comment="credits数量")
    price_cents = Column(Integer, nullable=False, comment="价格(分)")
    bonus_credits = Column(Integer, default=0, comment="赠送credits")
    is_popular = Column(Boolean, default=False, comment="是否热门")
    is_active = Column(Boolean, default=True, comment="是否启用")
    display_order = Column(Integer, default=0, comment="显示顺序")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.pack_id,
            "name": self.name,
            "credits": self.credits,
            "price_cents": self.price_cents,
            "bonus_credits": self.bonus_credits,
            "total_credits": self.credits + (self.bonus_credits or 0),
            "is_popular": self.is_popular,
            "is_active": self.is_active,
            "display_order": self.display_order,
        }


DEFAULT_CREDIT_PACKS = [
    {"pack_id": "pack_100", "name": "Starter", "credits": 100, "price_cents": 999, "bonus_credits": 0, "is_popular": False, "display_order": 1},
    {"pack_id": "pack_350", "name": "Popular", "credits": 350, "price_cents": 3499, "bonus_credits": 0, "is_popular": True, "display_order": 2},
    {"pack_id": "pack_550", "name": "Value", "credits": 550, "price_cents": 4999, "bonus_credits": 0, "is_popular": False, "display_order": 3},
    {"pack_id": "pack_1150", "name": "Power", "credits": 1150, "price_cents": 9999, "bonus_credits": 0, "is_popular": False, "display_order": 4},
    {"pack_id": "pack_2400", "name": "Big", "credits": 2400, "price_cents": 19999, "bonus_credits": 0, "is_popular": False, "display_order": 5},
    {"pack_id": "pack_3750", "name": "Ultimate", "credits": 3750, "price_cents": 29999, "bonus_credits": 0, "is_popular": False, "display_order": 6},
]
