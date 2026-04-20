"""
Database migration: add description column to lora_presets table.

Usage:
    python -m app.migrations.add_lora_description
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    from app.core.database import db

    logger.info("Adding description column to lora_presets...")
    try:
        await db.execute(
            "ALTER TABLE lora_presets ADD COLUMN description TEXT NOT NULL DEFAULT ''"
        )
        logger.info("Column added successfully.")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            logger.info("Column already exists, skipping.")
        else:
            raise
    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
