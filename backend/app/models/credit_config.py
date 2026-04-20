from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class CreditCostConfig(Base):
    __tablename__ = "credit_cost_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    message_cost = Column(Float, default=0.1, comment="文本消息消耗")
    voice_cost = Column(Float, default=0.2, comment="语音生成消耗")
    image_cost = Column(Integer, default=2, comment="图片生成消耗")
    video_cost = Column(Integer, default=4, comment="视频生成消耗")
    voice_call_per_minute = Column(Integer, default=3, comment="实时通话每分钟消耗")
    
    signup_bonus_credits = Column(Integer, default=10, comment="注册奖励credits")
    premium_monthly_credits = Column(Integer, default=100, comment="订阅用户每月credits")
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(255), nullable=True, comment="最后更新管理员")

    def to_dict(self):
        return {
            "message_cost": self.message_cost,
            "voice_cost": self.voice_cost,
            "image_cost": self.image_cost,
            "video_cost": self.video_cost,
            "voice_call_per_minute": self.voice_call_per_minute,
            "signup_bonus_credits": self.signup_bonus_credits,
            "premium_monthly_credits": self.premium_monthly_credits,
        }
