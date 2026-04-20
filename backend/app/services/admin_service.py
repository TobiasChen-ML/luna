import logging
import uuid
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import json

from ..core.config import get_settings
from .redis_service import RedisService
from .database_service import DatabaseService
from .task_service import TaskService
from ..models.admin import APIKeyModel, BatchJobModel

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(
        self,
        redis: Optional[RedisService] = None,
        db: Optional[DatabaseService] = None,
        task_service: Optional[TaskService] = None,
    ):
        self.settings = get_settings()
        self.redis = redis or RedisService()
        self.db = db or DatabaseService()
        self.task_service = task_service or TaskService()

    async def create_api_key(
        self,
        user_id: str,
        name: str,
        permissions: Optional[list[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> dict:
        key_id = str(uuid.uuid4())
        raw_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:8]
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        with self.db.get_session() as session:
            api_key = APIKeyModel(
                id=key_id,
                user_id=user_id,
                name=name,
                key_hash=key_hash,
                is_active=1,
                created_at=datetime.utcnow(),
            )
            session.add(api_key)
            session.commit()
        
        await self.redis.set(
            f"api_key:{key_id}",
            {
                "id": key_id,
                "user_id": user_id,
                "name": name,
                "key_prefix": key_prefix,
                "permissions": permissions or [],
                "expires_at": expires_at.isoformat() if expires_at else None,
                "is_active": True,
            },
        )
        
        return {
            "id": key_id,
            "name": name,
            "key": f"roxy_{key_prefix}_{raw_key[8:]}",
            "key_prefix": key_prefix,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
        }

    async def list_api_keys(self, user_id: str) -> list[dict]:
        keys = []
        
        with self.db.get_session() as session:
            api_keys = session.query(APIKeyModel).filter(
                APIKeyModel.user_id == user_id
            ).all()
            
            for key in api_keys:
                keys.append({
                    "id": key.id,
                    "name": key.name,
                    "is_active": bool(key.is_active),
                    "created_at": key.created_at.isoformat() if key.created_at else None,
                    "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                    "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
                })
        
        return keys

    async def revoke_api_key(self, key_id: str, user_id: str) -> dict:
        with self.db.get_session() as session:
            api_key = session.query(APIKeyModel).filter(
                APIKeyModel.id == key_id,
                APIKeyModel.user_id == user_id
            ).first()
            
            if api_key:
                api_key.is_active = 0
                api_key.revoked_at = datetime.utcnow()
                session.commit()
        
        await self.redis.delete(f"api_key:{key_id}")
        
        return {"key_id": key_id, "revoked": True}

    async def validate_api_key(self, raw_key: str) -> Optional[dict]:
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        with self.db.get_session() as session:
            api_key = session.query(APIKeyModel).filter(
                APIKeyModel.key_hash == key_hash,
                APIKeyModel.is_active == 1
            ).first()
            
            if api_key:
                api_key.last_used_at = datetime.utcnow()
                session.commit()
                
                return {
                    "id": api_key.id,
                    "user_id": api_key.user_id,
                    "name": api_key.name,
                }
        
        return None

    async def create_batch_job(
        self,
        user_id: str,
        job_type: str,
        config: dict,
        items: list[dict],
    ) -> dict:
        job_id = str(uuid.uuid4())
        
        with self.db.get_session() as session:
            batch_job = BatchJobModel(
                id=job_id,
                user_id=user_id,
                type=job_type,
                status="pending",
                total=len(items),
                config=json.dumps(config),
                created_at=datetime.utcnow(),
            )
            session.add(batch_job)
            session.commit()
        
        await self.redis.set(
            f"batch_job:{job_id}",
            {
                "id": job_id,
                "user_id": user_id,
                "type": job_type,
                "status": "pending",
                "total": len(items),
                "completed": 0,
                "failed": 0,
                "items": items,
            },
        )
        
        return {
            "job_id": job_id,
            "type": job_type,
            "total": len(items),
            "status": "pending",
        }

    async def get_batch_job(self, job_id: str) -> Optional[dict]:
        cached = await self.redis.get(f"batch_job:{job_id}")
        
        if cached:
            return cached
        
        with self.db.get_session() as session:
            batch_job = session.query(BatchJobModel).filter(
                BatchJobModel.id == job_id
            ).first()
            
            if batch_job:
                return {
                    "id": batch_job.id,
                    "user_id": batch_job.user_id,
                    "type": batch_job.type,
                    "status": batch_job.status,
                    "total": batch_job.total,
                    "completed": batch_job.completed,
                    "failed": batch_job.failed,
                    "config": json.loads(batch_job.config) if batch_job.config else {},
                    "created_at": batch_job.created_at.isoformat() if batch_job.created_at else None,
                }
        
        return None

    async def list_batch_jobs(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> list[dict]:
        jobs = []
        
        with self.db.get_session() as session:
            query = session.query(BatchJobModel).filter(
                BatchJobModel.user_id == user_id
            )
            
            if status:
                query = query.filter(BatchJobModel.status == status)
            
            batch_jobs = query.order_by(BatchJobModel.created_at.desc()).all()
            
            for job in batch_jobs:
                jobs.append({
                    "id": job.id,
                    "type": job.type,
                    "status": job.status,
                    "total": job.total,
                    "completed": job.completed,
                    "failed": job.failed,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                })
        
        return jobs

    async def create_seo_keywords(
        self,
        keywords: list[dict],
    ) -> dict:
        created = []
        
        for kw in keywords:
            keyword_id = str(uuid.uuid4())
            
            await self.redis.lpush(
                "seo_keywords:pending",
                json.dumps({
                    "id": keyword_id,
                    "keyword": kw.get("keyword"),
                    "category": kw.get("category"),
                }),
            )
            
            created.append(keyword_id)
        
        return {
            "created_count": len(created),
            "keywords": keywords,
        }

    async def get_seo_keywords(
        self,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        keywords = []
        
        items = await self.redis.lrange("seo_keywords:pending", 0, limit - 1)
        
        for item in items:
            try:
                kw = json.loads(item)
                if category and kw.get("category") != category:
                    continue
                keywords.append(kw)
            except json.JSONDecodeError:
                continue
        
        return keywords

    async def import_seo_keywords_csv(
        self,
        csv_content: str,
    ) -> dict:
        lines = csv_content.strip().split("\n")
        
        keywords = []
        for line in lines[1:]:
            parts = line.split(",")
            if len(parts) >= 1:
                keywords.append({
                    "keyword": parts[0].strip(),
                    "category": parts[1].strip() if len(parts) > 1 else None,
                })
        
        return await self.create_seo_keywords(keywords)

    async def health_check(self) -> dict:
        return {"status": "healthy"}