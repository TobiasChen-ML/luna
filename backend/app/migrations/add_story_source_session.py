"""
Database migration: add source_session_id and cover_image_url to scripts table.

Usage:
    python -m app.migrations.add_story_source_session
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    from app.core.database import db

    logger.info("Adding source_session_id and cover_image_url to scripts table...")

    for col_name, col_def in [
        ("source_session_id", "TEXT"),
        ("cover_image_url", "TEXT"),
    ]:
        try:
            await db.execute(f"ALTER TABLE scripts ADD COLUMN {col_name} {col_def}")
            logger.info(f"Column {col_name} added.")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                logger.info(f"Column {col_name} already exists, skipping.")
            else:
                raise

    try:
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_scripts_source_session ON scripts(source_session_id)"
        )
        logger.info("Index idx_scripts_source_session created.")
    except Exception as e:
        logger.warning(f"Index creation skipped: {e}")

    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
