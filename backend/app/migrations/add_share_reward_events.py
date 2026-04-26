"""
Migration: add share reward events table.

Usage:
    python -m app.migrations.add_share_reward_events
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import db

logger = logging.getLogger(__name__)


async def migrate():
    logger.info("Starting migration: add_share_reward_events")

    await db.execute(
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
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_share_reward_events_user_status_created "
        "ON share_reward_events(user_id, status, created_at)"
    )

    logger.info("Migration completed successfully")


if __name__ == "__main__":
    asyncio.run(migrate())
