"""
Migration: Add user preference tables for personalized recommendations

Tables:
- character_views: Track user browsing behavior
- character_favorites: User's favorite characters
- user_preference_profiles: Aggregated preference vectors
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.core.database import db

logger = logging.getLogger(__name__)


async def migrate():
    logger.info("Starting migration: add_user_preference_tables")
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS character_views (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            character_id TEXT NOT NULL,
            view_duration_seconds INTEGER DEFAULT 0,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("Created table: character_views")
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_character_views_user 
        ON character_views(user_id)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_character_views_character 
        ON character_views(character_id)
    """)
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS character_favorites (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            character_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, character_id)
        )
    """)
    logger.info("Created table: character_favorites")
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_character_favorites_user 
        ON character_favorites(user_id)
    """)
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_preference_profiles (
            user_id TEXT PRIMARY KEY,
            
            preferred_ethnicities TEXT,
            preferred_nationalities TEXT,
            preferred_occupations TEXT,
            preferred_personality_tags TEXT,
            preferred_age_range TEXT,
            preferred_appearance TEXT,
            
            total_interactions INTEGER DEFAULT 0,
            last_updated TIMESTAMP,
            
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    logger.info("Created table: user_preference_profiles")
    
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    asyncio.run(migrate())
