"""
Migration: Add trend and performance tracking tables

Tables:
- trend_keywords: Store trending search terms from Google Trends
- character_performance: Track character engagement metrics
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import db

logger = logging.getLogger(__name__)


async def migrate():
    logger.info("Starting migration: add_trend_tables")
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS trend_keywords (
            id TEXT PRIMARY KEY,
            keyword TEXT NOT NULL,
            source TEXT DEFAULT 'google_trends',
            search_volume INTEGER,
            trend_direction TEXT DEFAULT 'stable',
            category_mapping TEXT,
            relevance_score REAL DEFAULT 0.0,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)
    logger.info("Created table: trend_keywords")
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_trend_keywords_keyword 
        ON trend_keywords(keyword)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_trend_keywords_relevance 
        ON trend_keywords(relevance_score DESC)
    """)
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS character_performance (
            id TEXT PRIMARY KEY,
            character_id TEXT NOT NULL,
            date TEXT NOT NULL,
            views INTEGER DEFAULT 0,
            clicks INTEGER DEFAULT 0,
            chats_started INTEGER DEFAULT 0,
            avg_messages_per_chat REAL DEFAULT 0.0,
            retention_1d REAL DEFAULT 0.0,
            retention_7d REAL DEFAULT 0.0,
            UNIQUE(character_id, date)
        )
    """)
    logger.info("Created table: character_performance")
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_character_performance_character 
        ON character_performance(character_id)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_character_performance_date 
        ON character_performance(date)
    """)
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS generation_weights (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            attribute_key TEXT NOT NULL,
            attribute_value TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            source TEXT DEFAULT 'default',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, attribute_key, attribute_value)
        )
    """)
    logger.info("Created table: generation_weights")
    
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    asyncio.run(migrate())
