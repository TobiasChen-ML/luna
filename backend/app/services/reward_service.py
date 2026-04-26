import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text

from .database_service import DatabaseService
from .credit_service import credit_service as default_credit_service

logger = logging.getLogger(__name__)


SHARE_REWARD_AMOUNT = 10
MAX_DAILY_SHARE_REWARDS = 3
REWARD_TYPE_SHARE = "share"


class RewardService:
    def __init__(
        self,
        db: Optional[DatabaseService] = None,
        credit_svc=None,
    ):
        self.db = db or DatabaseService()
        self.credit_svc = credit_svc or default_credit_service
        self._schema_ready = False

    def _normalize_share_key(self, share_key: str) -> str:
        key = str(share_key or "").strip().lower()
        if not key:
            raise ValueError("share_key is required")
        if len(key) > 128:
            raise ValueError("share_key is too long")
        return key

    def _normalize_channel(self, channel: Optional[str]) -> str:
        value = str(channel or "").strip().lower()
        if not value:
            return "unknown"
        return value[:32]

    def _serialize_metadata(self, metadata: Optional[dict[str, Any]]) -> str:
        if not metadata:
            return "{}"
        try:
            return json.dumps(metadata, ensure_ascii=False)
        except Exception:
            return "{}"

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        with self.db.transaction() as session:
            session.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS share_reward_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        reward_type TEXT NOT NULL DEFAULT 'share',
                        share_key TEXT NOT NULL,
                        reward_amount INTEGER NOT NULL DEFAULT 10,
                        status TEXT NOT NULL DEFAULT 'pending',
                        channel TEXT,
                        metadata TEXT,
                        granted_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, reward_type, share_key)
                    )
                    """
                )
            )
            session.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_share_reward_events_user_status_created "
                    "ON share_reward_events(user_id, status, created_at)"
                )
            )
        self._schema_ready = True

    async def claim_share_reward(
        self,
        *,
        user_id: str,
        share_key: str,
        channel: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        normalized_key = self._normalize_share_key(share_key)
        normalized_channel = self._normalize_channel(channel)
        metadata_json = self._serialize_metadata(metadata)
        self._ensure_schema()

        with self.db.transaction() as session:
            existing = session.execute(
                text(
                    """
                    SELECT id, status
                    FROM share_reward_events
                    WHERE user_id = :user_id
                      AND reward_type = :reward_type
                      AND share_key = :share_key
                    LIMIT 1
                    """
                ),
                {
                    "user_id": user_id,
                    "reward_type": REWARD_TYPE_SHARE,
                    "share_key": normalized_key,
                },
            ).mappings().first()

            if existing and existing["status"] == "granted":
                balance = await self.credit_svc.get_balance(user_id)
                return {
                    "success": True,
                    "granted": False,
                    "reason": "duplicate",
                    "reward_amount": 0,
                    "new_balance": float(balance.get("total", 0)),
                }

            daily_count = session.execute(
                text(
                    """
                    SELECT COUNT(1) AS cnt
                    FROM share_reward_events
                    WHERE user_id = :user_id
                      AND reward_type = :reward_type
                      AND status = 'granted'
                      AND created_at >= :day_start
                    """
                ),
                {
                    "user_id": user_id,
                    "reward_type": REWARD_TYPE_SHARE,
                    "day_start": datetime.now(timezone.utc).replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    ).isoformat(),
                },
            ).scalar_one()

            if int(daily_count or 0) >= MAX_DAILY_SHARE_REWARDS:
                balance = await self.credit_svc.get_balance(user_id)
                return {
                    "success": True,
                    "granted": False,
                    "reason": "daily_limit",
                    "reward_amount": 0,
                    "new_balance": float(balance.get("total", 0)),
                    "daily_limit": MAX_DAILY_SHARE_REWARDS,
                }

            now_iso = datetime.now(timezone.utc).isoformat()
            if existing:
                session.execute(
                    text(
                        """
                        UPDATE share_reward_events
                        SET status = 'pending',
                            channel = :channel,
                            metadata = :metadata,
                            updated_at = :updated_at
                        WHERE id = :id
                        """
                    ),
                    {
                        "id": existing["id"],
                        "channel": normalized_channel,
                        "metadata": metadata_json,
                        "updated_at": now_iso,
                    },
                )
            else:
                session.execute(
                    text(
                        """
                        INSERT INTO share_reward_events
                            (user_id, reward_type, share_key, reward_amount, status, channel, metadata, updated_at)
                        VALUES
                            (:user_id, :reward_type, :share_key, :reward_amount, 'pending', :channel, :metadata, :updated_at)
                        """
                    ),
                    {
                        "user_id": user_id,
                        "reward_type": REWARD_TYPE_SHARE,
                        "share_key": normalized_key,
                        "reward_amount": SHARE_REWARD_AMOUNT,
                        "channel": normalized_channel,
                        "metadata": metadata_json,
                        "updated_at": now_iso,
                    },
                )

        try:
            await self.credit_svc.add_credits(
                user_id=user_id,
                amount=SHARE_REWARD_AMOUNT,
                transaction_type="share_reward",
                credit_source="purchased",
                order_id=f"share:{normalized_key}",
                description=f"Share reward ({normalized_channel})",
            )
        except Exception as exc:
            logger.error("Failed to grant share reward for user %s: %s", user_id, exc)
            with self.db.transaction() as session:
                session.execute(
                    text(
                        """
                        UPDATE share_reward_events
                        SET status = 'failed',
                            updated_at = :updated_at
                        WHERE user_id = :user_id
                          AND reward_type = :reward_type
                          AND share_key = :share_key
                        """
                    ),
                    {
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "user_id": user_id,
                        "reward_type": REWARD_TYPE_SHARE,
                        "share_key": normalized_key,
                    },
                )
            raise

        with self.db.transaction() as session:
            session.execute(
                text(
                    """
                    UPDATE share_reward_events
                    SET status = 'granted',
                        granted_at = :granted_at,
                        updated_at = :updated_at
                    WHERE user_id = :user_id
                      AND reward_type = :reward_type
                      AND share_key = :share_key
                    """
                ),
                {
                    "granted_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "user_id": user_id,
                    "reward_type": REWARD_TYPE_SHARE,
                    "share_key": normalized_key,
                },
            )

        balance = await self.credit_svc.get_balance(user_id)
        return {
            "success": True,
            "granted": True,
            "reason": "granted",
            "reward_amount": SHARE_REWARD_AMOUNT,
            "new_balance": float(balance.get("total", 0)),
        }


reward_service = RewardService()
