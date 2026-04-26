"""
Migration: Add review_status fields to characters table

Run with: python -m app.migrations.add_character_review_fields
"""

import asyncio
import sqlite3
from pathlib import Path


async def migrate():
    from app.core.config import resolve_sqlite_path, settings
    
    db_path = Path(resolve_sqlite_path(settings.database_url))
    
    print(f"Migrating database at: {db_path}")
    
    async with sqlite3.connect(str(db_path)) as db:
        cursor = await db.execute("PRAGMA table_info(characters)")
        columns = [row[1] for row in await cursor.fetchall()]
        
        if "review_status" not in columns:
            print("Adding review_status column...")
            await db.execute("ALTER TABLE characters ADD COLUMN review_status TEXT DEFAULT 'approved'")
        else:
            print("review_status column already exists")
        
        if "reviewed_at" not in columns:
            print("Adding reviewed_at column...")
            await db.execute("ALTER TABLE characters ADD COLUMN reviewed_at TIMESTAMP")
        else:
            print("reviewed_at column already exists")
        
        if "reviewer_id" not in columns:
            print("Adding reviewer_id column...")
            await db.execute("ALTER TABLE characters ADD COLUMN reviewer_id TEXT")
        else:
            print("reviewer_id column already exists")
        
        if "rejection_reason" not in columns:
            print("Adding rejection_reason column...")
            await db.execute("ALTER TABLE characters ADD COLUMN rejection_reason TEXT")
        else:
            print("rejection_reason column already exists")
        
        await db.commit()
    
    print("Migration complete!")


if __name__ == "__main__":
    import aiosqlite
    asyncio.run(migrate())
