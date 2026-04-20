"""
Migration: Add ethnicity, nationality, occupation fields to characters table

Run with: python -m app.migrations.add_character_diversity_fields
"""

import asyncio
import aiosqlite
from pathlib import Path


async def migrate():
    from app.core.config import settings
    
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    
    print(f"Migrating database at: {db_path}")
    
    async with aiosqlite.connect(str(db_path)) as db:
        cursor = await db.execute("PRAGMA table_info(characters)")
        rows = await cursor.fetchall()
        columns = [row[1] for row in rows]
        
        if "ethnicity" not in columns:
            print("Adding ethnicity column...")
            await db.execute("ALTER TABLE characters ADD COLUMN ethnicity TEXT")
        else:
            print("ethnicity column already exists")
        
        if "nationality" not in columns:
            print("Adding nationality column...")
            await db.execute("ALTER TABLE characters ADD COLUMN nationality TEXT")
        else:
            print("nationality column already exists")
        
        if "occupation" not in columns:
            print("Adding occupation column...")
            await db.execute("ALTER TABLE characters ADD COLUMN occupation TEXT")
        else:
            print("occupation column already exists")
        
        await db.commit()
    
    print("Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())
