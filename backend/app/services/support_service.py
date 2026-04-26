import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text

from .database_service import DatabaseService
from .redis_service import RedisService

logger = logging.getLogger(__name__)


ALLOWED_ISSUE_TYPES = {"missed_credits", "duplicate_charge", "other"}
ALLOWED_STATUS = {"open", "in_progress", "resolved", "closed"}


class SupportService:
    def __init__(self, db: Optional[DatabaseService] = None, redis: Optional[RedisService] = None):
        self.db = db or DatabaseService()
        self.redis = redis or RedisService()
        self._schema_ready = False

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return

        with self.db.transaction() as session:
            session.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS support_tickets (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        user_email TEXT NOT NULL,
                        order_id TEXT,
                        issue_type TEXT NOT NULL DEFAULT 'other',
                        subject TEXT,
                        message TEXT NOT NULL,
                        category TEXT,
                        priority TEXT DEFAULT 'normal',
                        status TEXT NOT NULL DEFAULT 'open',
                        credits_granted REAL,
                        resolution TEXT,
                        resolved_by TEXT,
                        resolved_at TIMESTAMP,
                        feedback_rating INTEGER,
                        feedback_comment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            session.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_support_tickets_user_created "
                    "ON support_tickets(user_id, created_at DESC)"
                )
            )
            session.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_support_tickets_status_created "
                    "ON support_tickets(status, created_at DESC)"
                )
            )

        self._schema_ready = True

    @staticmethod
    def _normalize_issue_type(value: Optional[str]) -> str:
        normalized = (value or "other").strip().lower()
        if normalized not in ALLOWED_ISSUE_TYPES:
            return "other"
        return normalized

    @staticmethod
    def _normalize_status(value: Optional[str]) -> str:
        normalized = (value or "open").strip().lower()
        if normalized not in ALLOWED_STATUS:
            return "open"
        return normalized

    async def create_ticket(
        self,
        *,
        user_id: str,
        user_email: str,
        issue_type: Optional[str] = None,
        message: str,
        order_id: Optional[str] = None,
        subject: Optional[str] = None,
        category: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> dict[str, Any]:
        self._ensure_schema()

        clean_message = (message or "").strip()
        if len(clean_message) < 10:
            raise ValueError("description/message must be at least 10 characters")

        ticket_id = f"tkt_{uuid.uuid4().hex[:20]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        normalized_issue_type = self._normalize_issue_type(issue_type or category)

        with self.db.transaction() as session:
            session.execute(
                text(
                    """
                    INSERT INTO support_tickets (
                        id, user_id, user_email, order_id, issue_type,
                        subject, message, category, priority, status, created_at, updated_at
                    ) VALUES (
                        :id, :user_id, :user_email, :order_id, :issue_type,
                        :subject, :message, :category, :priority, 'open', :created_at, :updated_at
                    )
                    """
                ),
                {
                    "id": ticket_id,
                    "user_id": user_id,
                    "user_email": user_email,
                    "order_id": (order_id or "").strip() or None,
                    "issue_type": normalized_issue_type,
                    "subject": (subject or "").strip() or normalized_issue_type,
                    "message": clean_message,
                    "category": (category or "").strip() or None,
                    "priority": (priority or "normal").strip().lower(),
                    "created_at": now_iso,
                    "updated_at": now_iso,
                },
            )

        await self._publish_ticket_event(
            event_type="support_ticket_created",
            user_id=user_id,
            payload={
                "ticket_id": ticket_id,
                "status": "open",
                "issue_type": normalized_issue_type,
                "order_id": (order_id or "").strip() or None,
                "created_at": now_iso,
            },
        )
        return {"id": ticket_id, "status": "open"}

    async def list_user_tickets(self, *, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        self._ensure_schema()
        with self.db.transaction() as session:
            rows = (
                session.execute(
                    text(
                        """
                        SELECT id, user_email, order_id, issue_type, message,
                               status, credits_granted, created_at
                        FROM support_tickets
                        WHERE user_id = :user_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"user_id": user_id, "limit": max(1, min(limit, 200))},
                )
                .mappings()
                .all()
            )
        return [dict(row) for row in rows]

    async def list_admin_tickets(
        self,
        *,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        self._ensure_schema()
        normalized_status = self._normalize_status(status) if status else None
        with self.db.transaction() as session:
            if normalized_status:
                rows = (
                    session.execute(
                        text(
                            """
                            SELECT *
                            FROM support_tickets
                            WHERE status = :status
                            ORDER BY created_at DESC
                            LIMIT :limit
                            """
                        ),
                        {"status": normalized_status, "limit": max(1, min(limit, 500))},
                    )
                    .mappings()
                    .all()
                )
            else:
                rows = (
                    session.execute(
                        text(
                            """
                            SELECT *
                            FROM support_tickets
                            ORDER BY created_at DESC
                            LIMIT :limit
                            """
                        ),
                        {"limit": max(1, min(limit, 500))},
                    )
                    .mappings()
                    .all()
                )
        return [dict(row) for row in rows]

    async def resolve_ticket(
        self,
        *,
        ticket_id: str,
        admin_email: str,
        resolution: Optional[str] = None,
        credits_granted: Optional[float] = None,
        status: str = "resolved",
    ) -> dict[str, Any]:
        self._ensure_schema()
        now_iso = datetime.now(timezone.utc).isoformat()
        normalized_status = self._normalize_status(status)
        with self.db.transaction() as session:
            existing = (
                session.execute(
                    text("SELECT id FROM support_tickets WHERE id = :id"),
                    {"id": ticket_id},
                )
                .mappings()
                .first()
            )
            if not existing:
                raise ValueError("Ticket not found")

            session.execute(
                text(
                    """
                    UPDATE support_tickets
                    SET status = :status,
                        resolution = :resolution,
                        credits_granted = :credits_granted,
                        resolved_by = :resolved_by,
                        resolved_at = :resolved_at,
                        updated_at = :updated_at
                    WHERE id = :id
                    """
                ),
                {
                    "id": ticket_id,
                    "status": normalized_status,
                    "resolution": (resolution or "").strip() or None,
                    "credits_granted": credits_granted,
                    "resolved_by": admin_email,
                    "resolved_at": now_iso,
                    "updated_at": now_iso,
                },
            )

        await self._publish_ticket_event(
            event_type="support_ticket_resolved",
            user_id=None,
            payload={
                "ticket_id": ticket_id,
                "status": normalized_status,
                "resolved_by": admin_email,
                "credits_granted": credits_granted,
                "resolved_at": now_iso,
                "resolution": (resolution or "").strip() or None,
            },
        )
        return {"id": ticket_id, "status": normalized_status}

    async def submit_feedback(
        self,
        *,
        user_id: str,
        user_email: str,
        rating: Optional[int],
        comment: Optional[str],
        feedback_type: Optional[str] = None,
    ) -> dict[str, Any]:
        self._ensure_schema()
        message = (comment or "").strip()
        if len(message) < 3:
            raise ValueError("feedback comment is too short")

        # Persist feedback as a dedicated support ticket row so it is visible in admin queue.
        return await self.create_ticket(
            user_id=user_id,
            user_email=user_email,
            issue_type="other",
            message=f"[feedback:{(feedback_type or 'general').strip().lower()}] {message}",
            subject="User feedback",
            category="feedback",
            priority="low",
        )

    async def _publish_ticket_event(
        self,
        *,
        event_type: str,
        user_id: Optional[str],
        payload: dict[str, Any],
    ) -> None:
        event = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            if user_id:
                await self.redis.publish_json(f"events:user:{user_id}", event)
            await self.redis.publish_json("events:support", event)
        except Exception as exc:
            logger.warning(f"Failed to publish support event {event_type}: {exc}")


support_service = SupportService()
