"""
Database migration script for Script Review and Story Replay system.

Run this script to add script_reviews, story_progress, story_nodes, and stories tables.

Usage:
    python -m app.migrations.add_script_review_system
"""

import asyncio
import logging
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    from app.core.config import settings
    
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting script review system migration on {db_path}...")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='script_reviews'")
        if cursor.fetchone():
            logger.info("script_reviews table already exists, skipping...")
        else:
            cursor.execute("""
                CREATE TABLE script_reviews (
                    id TEXT PRIMARY KEY,
                    script_id TEXT NOT NULL,
                    reviewer_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    previous_status TEXT,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (script_id) REFERENCES scripts(id)
                )
            """)
            cursor.execute("CREATE INDEX idx_reviews_script ON script_reviews(script_id)")
            cursor.execute("CREATE INDEX idx_reviews_action ON script_reviews(action)")
            logger.info("Created script_reviews table")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='story_progress'")
        if cursor.fetchone():
            logger.info("story_progress table already exists, skipping...")
        else:
            cursor.execute("""
                CREATE TABLE story_progress (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    story_id TEXT NOT NULL,
                    character_id TEXT NOT NULL,
                    status TEXT DEFAULT 'in_progress',
                    current_node_id TEXT,
                    visited_nodes TEXT,
                    choices_made TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    ending_type TEXT,
                    completion_time_minutes INTEGER,
                    archived INTEGER DEFAULT 0,
                    play_index INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (story_id) REFERENCES scripts(id)
                )
            """)
            cursor.execute("CREATE INDEX idx_story_progress_user ON story_progress(user_id)")
            cursor.execute("CREATE INDEX idx_story_progress_story ON story_progress(story_id)")
            cursor.execute("CREATE INDEX idx_story_progress_archived ON story_progress(archived)")
            logger.info("Created story_progress table")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='story_nodes'")
        if cursor.fetchone():
            logger.info("story_nodes table already exists, skipping...")
        else:
            cursor.execute("""
                CREATE TABLE story_nodes (
                    id TEXT PRIMARY KEY,
                    story_id TEXT NOT NULL,
                    sequence INTEGER DEFAULT 0,
                    title TEXT,
                    narrative_phase TEXT DEFAULT 'opening',
                    location TEXT,
                    scene_description TEXT,
                    character_context TEXT,
                    response_instructions TEXT,
                    max_turns_in_node INTEGER DEFAULT 3,
                    choices TEXT,
                    auto_advance TEXT,
                    is_ending_node INTEGER DEFAULT 0,
                    ending_type TEXT,
                    trigger_image INTEGER DEFAULT 0,
                    image_prompt_hint TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (story_id) REFERENCES scripts(id)
                )
            """)
            cursor.execute("CREATE INDEX idx_story_nodes_story ON story_nodes(story_id)")
            logger.info("Created story_nodes table")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stories'")
        if cursor.fetchone():
            logger.info("stories table already exists, skipping...")
        else:
            cursor.execute("""
                CREATE TABLE stories (
                    id TEXT PRIMARY KEY,
                    character_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    slug TEXT UNIQUE,
                    description TEXT,
                    cover_image_url TEXT,
                    author_type TEXT DEFAULT 'admin',
                    author_id TEXT,
                    status TEXT DEFAULT 'draft',
                    is_official INTEGER DEFAULT 0,
                    entry_conditions TEXT,
                    start_node_id TEXT,
                    total_nodes INTEGER DEFAULT 0,
                    ai_trigger_keywords TEXT,
                    completion_rewards TEXT,
                    play_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (character_id) REFERENCES characters(id)
                )
            """)
            cursor.execute("CREATE INDEX idx_stories_character ON stories(character_id)")
            cursor.execute("CREATE INDEX idx_stories_status ON stories(status)")
            logger.info("Created stories table")

        cursor.execute("PRAGMA table_info(scripts)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'total_plays' not in columns:
            cursor.execute("ALTER TABLE scripts ADD COLUMN total_plays INTEGER DEFAULT 0")
            logger.info("Added total_plays column to scripts table")
        
        conn.commit()
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    asyncio.run(migrate())
