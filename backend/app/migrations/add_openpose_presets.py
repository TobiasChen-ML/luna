"""Database migration: add openpose_presets table."""

import asyncio
import logging

from app.core.database import db

logger = logging.getLogger(__name__)


async def migrate() -> None:
    await db.execute(
        """CREATE TABLE IF NOT EXISTS openpose_presets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            image_url TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_openpose_presets_active ON openpose_presets(is_active)"
    )
    logger.info("openpose_presets table created (or already exists)")


if __name__ == "__main__":
    asyncio.run(migrate())
