"""
Database migration script for Memory system importance and decay.

Adds:
- importance: Initial importance score (1-10)
- decayed_importance: Time-decayed importance value
- last_accessed: Last access timestamp for decay calculation
- global_memories table for cross-character memory sharing

Usage:
    python -m app.migrations.add_memory_importance
"""

import asyncio
import logging
import aiosqlite
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    from app.core.config import settings
    
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    logger.info(f"Starting memory importance migration on {db_path}...")
    
    async with aiosqlite.connect(db_path) as db:
        try:
            await migrate_memories_table(db)
            await create_global_memories_table(db)
            await db.commit()
            logger.info("Migration completed successfully!")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise


async def migrate_memories_table(db: aiosqlite.Connection):
    cursor = await db.execute("PRAGMA table_info(memories)")
    columns = [row[1] for row in await cursor.fetchall()]
    
    new_columns = [
        ("importance", "INTEGER DEFAULT 5"),
        ("decayed_importance", "REAL DEFAULT 5.0"),
        ("last_accessed", "TIMESTAMP"),
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            await db.execute(f"ALTER TABLE memories ADD COLUMN {col_name} {col_type}")
            logger.info(f"Added column {col_name} to memories table")
    
    await db.execute("""
        UPDATE memories 
        SET importance = 5, 
            decayed_importance = 5.0,
            last_accessed = created_at
        WHERE importance IS NULL
    """)
    logger.info("Initialized default importance values for existing memories")


async def create_global_memories_table(db: aiosqlite.Connection):
    await db.execute("""
        CREATE TABLE IF NOT EXISTS global_memories (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'preference',
            source_character_id TEXT,
            confidence REAL DEFAULT 1.0,
            reference_count INTEGER DEFAULT 1,
            is_confirmed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    logger.info("Created global_memories table")
    
    await db.execute("CREATE INDEX IF NOT EXISTS idx_global_memories_user ON global_memories(user_id)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_global_memories_category ON global_memories(category)")


if __name__ == "__main__":
    asyncio.run(migrate())
