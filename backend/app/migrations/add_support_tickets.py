"""
Migration: add support tickets table.

Usage:
    python -m app.migrations.add_support_tickets
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import db

logger = logging.getLogger(__name__)


async def migrate():
    logger.info("Starting migration: add_support_tickets")

    await db.execute(
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
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_support_tickets_user_created "
        "ON support_tickets(user_id, created_at)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_support_tickets_status_created "
        "ON support_tickets(status, created_at)"
    )

    logger.info("Migration completed successfully")


if __name__ == "__main__":
    asyncio.run(migrate())
