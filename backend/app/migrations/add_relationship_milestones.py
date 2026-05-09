"""
Database migration: create relationship_milestones table.

Usage:
    python -m app.migrations.add_relationship_milestones
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    from app.core.database import db

    logger.info("Creating relationship_milestones table...")
    try:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS relationship_milestones (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                character_id TEXT NOT NULL,
                milestone_type TEXT NOT NULL,
                description TEXT,
                occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        logger.info("Table relationship_milestones created (or already exists).")
    except Exception as e:
        logger.error(f"Failed to create table: {e}")
        raise

    try:
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_milestones_user_char ON relationship_milestones (user_id, character_id)"
        )
        logger.info("Index created.")
    except Exception as e:
        logger.warning(f"Index creation skipped: {e}")

    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
