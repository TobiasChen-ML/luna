"""
Migration: Sync script tags from config/script_tags.json into database
Run: python -m app.migrations.sync_script_tags
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import db

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "config", "script_tags.json")


async def sync_tags():
    print(f"Reading tags from: {CONFIG_PATH}")
    
    if not os.path.exists(CONFIG_PATH):
        print(f"ERROR: {CONFIG_PATH} not found!")
        return
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        tags_config = json.load(f)
    
    await db.connect()
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS script_tags (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            name_en TEXT,
            description TEXT,
            examples TEXT,
            parent_id TEXT
        )
    """)
    
    added = 0
    updated = 0
    
    for category, tags in tags_config.items():
        for tag in tags:
            tag_id = tag.get("id", f"{category}_{tag.get('name', '')}")
            name = tag.get("name", "")
            name_en = tag.get("name_en", "")
            description = tag.get("description", "")
            examples = json.dumps(tag.get("examples", [])) if tag.get("examples") else None
            parent_id = tag.get("parent")
            
            existing = await db.execute(
                "SELECT id FROM script_tags WHERE id = ?",
                (tag_id,),
                fetch=True
            )
            
            if existing:
                await db.execute(
                    """UPDATE script_tags SET category = ?, name = ?, name_en = ?, description = ?, examples = ?, parent_id = ?
                       WHERE id = ?""",
                    (category, name, name_en, description, examples, parent_id, tag_id)
                )
                updated += 1
            else:
                await db.execute(
                    """INSERT INTO script_tags (id, category, name, name_en, description, examples, parent_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (tag_id, category, name, name_en, description, examples, parent_id)
                )
                added += 1
    
    count_result = await db.execute("SELECT COUNT(*) as count FROM script_tags", fetch=True)
    total = count_result['count'] if count_result else 0
    
    print(f"Done! Added {added} new tags, updated {updated} existing tags. Total: {total}")


if __name__ == "__main__":
    asyncio.run(sync_tags())
