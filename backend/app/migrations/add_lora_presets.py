"""
Database migration: add lora_presets table.

Usage:
    python -m app.migrations.add_lora_presets
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    from app.core.database import db

    logger.info("Starting lora_presets migration...")
    await db.execute("""
        CREATE TABLE IF NOT EXISTS lora_presets (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            model_name TEXT NOT NULL,
            strength REAL NOT NULL DEFAULT 0.8,
            trigger_word TEXT NOT NULL DEFAULT '',
            applies_to TEXT NOT NULL DEFAULT 'all',
            provider TEXT NOT NULL DEFAULT 'novita',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("lora_presets table created (or already exists)")
    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
