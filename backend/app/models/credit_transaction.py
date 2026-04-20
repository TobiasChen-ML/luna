from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Index

from .user import Base


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, index=True)
    
    transaction_type = Column(String(30), nullable=False)
    amount = Column(Float, nullable=False)
    balance_after = Column(Float, nullable=False)
    
    usage_type = Column(String(30), nullable=True)
    credit_source = Column(String(20), nullable=True)
    
    order_id = Column(String(100), nullable=True)
    character_id = Column(String(100), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('ix_credit_transactions_user_created', 'user_id', 'created_at'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "transaction_type": self.transaction_type,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "usage_type": self.usage_type,
            "credit_source": self.credit_source,
            "order_id": self.order_id,
            "character_id": self.character_id,
            "session_id": self.session_id,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
