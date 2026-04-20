from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(64), unique=True, index=True, nullable=False)
    
    task_type = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=False)
    
    status = Column(String(20), default="pending")
    progress = Column(Float, default=0.0)
    
    input_data = Column(JSON, nullable=True)
    result_url = Column(String(512), nullable=True)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    user_id = Column(Integer, nullable=True)
    character_id = Column(Integer, nullable=True)
    
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    webhook_received = Column(Boolean, default=False)
    webhook_payload = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class TaskCreate(BaseModel):
    task_type: str
    provider: str
    input_data: Optional[dict[str, Any]] = None
    user_id: Optional[int] = None
    character_id: Optional[int] = None


class TaskUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[float] = None
    result_url: Optional[str] = None
    result_data: Optional[dict] = None
    error_message: Optional[str] = None
    webhook_received: Optional[bool] = None
    webhook_payload: Optional[dict] = None


class TaskResponse(BaseModel):
    task_id: str
    task_type: str
    provider: str
    status: str
    progress: float
    result_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int
    page: int
    page_size: int