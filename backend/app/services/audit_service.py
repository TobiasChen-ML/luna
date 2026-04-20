import logging
import json
import uuid
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .database_service import DatabaseService
from ..core.database import db

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    CHARACTER_CREATE = "character_create"
    CHARACTER_UPDATE = "character_update"
    CHARACTER_DELETE = "character_delete"
    CHARACTER_BATCH_DELETE = "character_batch_delete"
    CHARACTER_APPROVE = "character_approve"
    CHARACTER_REJECT = "character_reject"
    CHARACTER_REGENERATE_IMAGES = "character_regenerate_images"
    
    CREDIT_CONFIG_UPDATE = "credit_config_update"
    CREDIT_ADJUST = "credit_adjust"
    CREDIT_BATCH_ADJUST = "credit_batch_adjust"
    CREDIT_PACK_CREATE = "credit_pack_create"
    CREDIT_PACK_UPDATE = "credit_pack_update"
    CREDIT_PACK_DELETE = "credit_pack_delete"
    SUBSCRIPTION_PLAN_UPDATE = "subscription_plan_update"
    
    USER_BAN = "user_ban"
    USER_UNBAN = "user_unban"
    
    PROMPT_CREATE = "prompt_create"
    PROMPT_UPDATE = "prompt_update"
    PROMPT_DELETE = "prompt_delete"
    
    SCRIPT_CREATE = "script_create"
    SCRIPT_UPDATE = "script_update"
    SCRIPT_DELETE = "script_delete"
    
    CONFIG_UPDATE = "config_update"
    
    API_KEY_CREATE = "api_key_create"
    API_KEY_REVOKE = "api_key_revoke"


@dataclass
class AuditLog:
    id: Optional[int] = None
    admin_id: str = ""
    admin_email: str = ""
    action: str = ""
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "admin_email": self.admin_email,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditService:
    def __init__(self):
        pass
    
    async def log_action(
        self,
        admin_id: str,
        admin_email: str,
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        old_value: Optional[Any] = None,
        new_value: Optional[Any] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> int:
        old_value_str = json.dumps(old_value, default=str) if old_value else None
        new_value_str = json.dumps(new_value, default=str) if new_value else None
        metadata_str = json.dumps(metadata, default=str) if metadata else None
        
        query = """
            INSERT INTO audit_logs (
                admin_id, admin_email, action, resource_type, resource_id,
                old_value, new_value, ip_address, user_agent, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        log_id = await db.execute(
            query,
            (
                admin_id,
                admin_email,
                action,
                resource_type,
                resource_id,
                old_value_str,
                new_value_str,
                ip_address,
                user_agent,
                metadata_str,
                datetime.utcnow(),
            ),
        )
        
        logger.info(
            f"Audit log: admin={admin_email} action={action} resource={resource_type}:{resource_id}"
        )
        
        return log_id
    
    async def get_logs(
        self,
        admin_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        conditions = []
        params = []
        
        if admin_id:
            conditions.append("admin_id = ?")
            params.append(admin_id)
        
        if action:
            conditions.append("action = ?")
            params.append(action)
        
        if resource_type:
            conditions.append("resource_type = ?")
            params.append(resource_type)
        
        if resource_id:
            conditions.append("resource_id = ?")
            params.append(resource_id)
        
        if start_date:
            conditions.append("created_at >= ?")
            params.append(start_date.isoformat())
        
        if end_date:
            conditions.append("created_at <= ?")
            params.append(end_date.isoformat())
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        count_query = f"SELECT COUNT(*) as count FROM audit_logs {where_clause}"
        count_result = await db.execute(count_query, tuple(params), fetch=True)
        total = count_result["count"] if count_result else 0
        
        query = f"""
            SELECT * FROM audit_logs
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        
        rows = await db.execute(query, tuple(params), fetch_all=True)
        
        logs = []
        for row in rows or []:
            logs.append(AuditLog(
                id=row.get("id"),
                admin_id=row.get("admin_id", ""),
                admin_email=row.get("admin_email", ""),
                action=row.get("action", ""),
                resource_type=row.get("resource_type"),
                resource_id=row.get("resource_id"),
                old_value=row.get("old_value"),
                new_value=row.get("new_value"),
                ip_address=row.get("ip_address"),
                user_agent=row.get("user_agent"),
                metadata=row.get("metadata"),
                created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
            ))
        
        return logs, total
    
    async def get_log_by_id(self, log_id: int) -> Optional[AuditLog]:
        query = "SELECT * FROM audit_logs WHERE id = ?"
        row = await db.execute(query, (log_id,), fetch=True)
        
        if not row:
            return None
        
        return AuditLog(
            id=row.get("id"),
            admin_id=row.get("admin_id", ""),
            admin_email=row.get("admin_email", ""),
            action=row.get("action", ""),
            resource_type=row.get("resource_type"),
            resource_id=row.get("resource_id"),
            old_value=row.get("old_value"),
            new_value=row.get("new_value"),
            ip_address=row.get("ip_address"),
            user_agent=row.get("user_agent"),
            metadata=row.get("metadata"),
            created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None,
        )
    
    async def get_admin_activity_summary(
        self,
        admin_id: Optional[str] = None,
        days: int = 30,
    ) -> dict:
        start_date = datetime.utcnow() - __import__('datetime').timedelta(days=days)
        
        conditions = ["created_at >= ?"]
        params = [start_date.isoformat()]
        
        if admin_id:
            conditions.append("admin_id = ?")
            params.append(admin_id)
        
        where_clause = f"WHERE {' AND '.join(conditions)}"
        
        query = f"""
            SELECT action, COUNT(*) as count
            FROM audit_logs
            {where_clause}
            GROUP BY action
            ORDER BY count DESC
        """
        
        rows = await db.execute(query, tuple(params), fetch_all=True)
        
        summary = {
            "total_actions": 0,
            "by_action": {},
            "by_admin": {},
        }
        
        for row in rows or []:
            action = row.get("action", "")
            count = row.get("count", 0)
            summary["by_action"][action] = count
            summary["total_actions"] += count
        
        admin_query = f"""
            SELECT admin_id, admin_email, COUNT(*) as count
            FROM audit_logs
            {where_clause}
            GROUP BY admin_id, admin_email
            ORDER BY count DESC
            LIMIT 10
        """
        
        admin_rows = await db.execute(admin_query, tuple(params), fetch_all=True)
        
        for row in admin_rows or []:
            admin_id_key = row.get("admin_id", "")
            summary["by_admin"][admin_id_key] = {
                "email": row.get("admin_email", ""),
                "count": row.get("count", 0),
            }
        
        return summary


audit_service = AuditService()
