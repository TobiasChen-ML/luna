import uuid
import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy import desc
from ..core.config import get_settings
from ..models.task import Task

logger = logging.getLogger(__name__)

FINAL_STATES = {"completed", "failed", "cancelled"}
STATE_PRIORITY = {"pending": 0, "processing": 1, "completed": 2, "failed": 2, "cancelled": 2}


class TaskService:
    def __init__(self, db_service=None, redis_service=None):
        self.settings = get_settings()
        self.db = db_service
        self.redis = redis_service
    
    def generate_task_id(self) -> str:
        return f"task_{uuid.uuid4().hex[:12]}"
    
    def _can_transition(self, current_status: str, new_status: str) -> bool:
        if current_status in FINAL_STATES:
            return False
        current_priority = STATE_PRIORITY.get(current_status, 0)
        new_priority = STATE_PRIORITY.get(new_status, 0)
        return new_priority >= current_priority
    
    async def create_task(
        self,
        task_type: str,
        provider: str,
        input_data: Optional[dict] = None,
        user_id: Optional[int] = None,
        character_id: Optional[int] = None
    ) -> Task:
        task_id = self.generate_task_id()
        
        with self.db.get_session() as session:
            task = Task(
                task_id=task_id,
                task_type=task_type,
                provider=provider,
                input_data=input_data,
                user_id=user_id,
                character_id=character_id,
                status="pending",
                progress=0.0
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            
            if self.redis:
                await self.redis.set_task_cache(task_id, {
                    "task_id": task_id,
                    "task_type": task_type,
                    "provider": provider,
                    "status": "pending",
                    "progress": 0.0,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                })
            
            return task
    
    async def get_task(self, task_id: str) -> Optional[Task]:
        if self.redis:
            cached = await self.redis.get_task_cache(task_id)
            if cached:
                return cached
        
        with self.db.get_session() as session:
            task = session.query(Task).filter(Task.task_id == task_id).first()
            if task and self.redis:
                await self.redis.set_task_cache(task_id, {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "provider": task.provider,
                    "status": task.status,
                    "progress": task.progress,
                    "result_url": task.result_url,
                    "error_message": task.error_message,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                })
            return task
    
    async def update_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        result_url: Optional[str] = None,
        result_data: Optional[dict] = None,
        error_message: Optional[str] = None
    ) -> Optional[Task]:
        with self.db.get_session() as session:
            task = session.query(Task).filter(Task.task_id == task_id).first()
            if not task:
                return None
            
            if status and not self._can_transition(task.status, status):
                logger.warning(f"Task {task_id}: Cannot transition from {task.status} to {status}")
                return task
            
            if status:
                task.status = status
            if progress is not None:
                task.progress = progress
            if result_url:
                task.result_url = result_url
            if result_data:
                task.result_data = result_data
            if error_message:
                task.error_message = error_message
            
            if status in FINAL_STATES:
                task.completed_at = datetime.utcnow()
            
            session.commit()
            session.refresh(task)
            
            if self.redis:
                await self.redis.set_task_cache(task_id, {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "provider": task.provider,
                    "status": task.status,
                    "progress": task.progress,
                    "result_url": task.result_url,
                    "error_message": task.error_message,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None
                })
            
            return task
    
    async def handle_webhook(self, task_id: str, payload: dict) -> Optional[Task]:
        with self.db.get_session() as session:
            task = session.query(Task).filter(Task.task_id == task_id).first()
            if not task:
                return None
            
            if task.status in FINAL_STATES:
                logger.info(f"Task {task_id} already in final state: {task.status}")
                return task
            
            task.webhook_received = True
            task.webhook_payload = payload
            
            provider_status = payload.get("status")
            if provider_status == "completed":
                task.status = "completed"
                task.progress = 100.0
                task.completed_at = datetime.utcnow()
                if "result_url" in payload:
                    task.result_url = payload["result_url"]
                if "result" in payload:
                    task.result_data = payload["result"]
            elif provider_status == "failed":
                task.status = "failed"
                task.error_message = payload.get("error", "Unknown error")
                task.completed_at = datetime.utcnow()
            
            session.commit()
            session.refresh(task)
            
            if self.redis:
                await self.redis.delete(f"task:{task_id}")
            
            return task
    
    async def list_tasks(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[Task], int]:
        with self.db.get_session() as session:
            query = session.query(Task)
            
            if user_id:
                query = query.filter(Task.user_id == user_id)
            if status:
                query = query.filter(Task.status == status)
            
            query = query.order_by(desc(Task.created_at))
            total = query.count()
            tasks = query.offset((page - 1) * page_size).limit(page_size).all()
            
            return tasks, total
    
    async def cleanup_old_tasks(self, days: int = 30) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        with self.db.get_session() as session:
            result = session.query(Task).filter(
                Task.status.in_(["completed", "failed"]),
                Task.completed_at < cutoff
            ).delete()
            session.commit()
            return result