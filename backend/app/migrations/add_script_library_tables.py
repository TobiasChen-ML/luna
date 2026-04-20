"""
Script Library Database Migration
Adds tables for script library management
"""
import asyncio
import json
from datetime import datetime
from app.core.database import db


async def migrate():
    print("Starting script library migration...")
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS script_library (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            title_en TEXT,
            summary TEXT,
            
            emotion_tones TEXT,
            relation_types TEXT,
            contrast_types TEXT,
            era TEXT,
            gender_target TEXT,
            character_gender TEXT,
            profession TEXT,
            length TEXT,
            age_rating TEXT,
            
            contrast_surface TEXT,
            contrast_truth TEXT,
            contrast_hook TEXT,
            
            script_seed TEXT,
            full_script TEXT,
            
            popularity INTEGER DEFAULT 0,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created script_library table")
    
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
    print("Created script_tags table")
    
    await db.execute("""
        CREATE TABLE IF NOT EXISTS script_tag_relations (
            script_id TEXT NOT NULL,
            tag_id TEXT NOT NULL,
            PRIMARY KEY (script_id, tag_id)
        )
    """)
    print("Created script_tag_relations table")
    
    await _load_tags_from_config()
    await _load_seeds_from_files()
    
    print("Script library migration completed!")


async def _load_tags_from_config():
    import os
    config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "script_tags.json")
    
    if not os.path.exists(config_path):
        print("Warning: script_tags.json not found, skipping tag import")
        return
    
    with open(config_path, "r", encoding="utf-8") as f:
        tags_config = json.load(f)
    
    tag_count = 0
    for category, tags in tags_config.items():
        for tag in tags:
            tag_id = tag.get("id", f"{category}_{tag.get('name', '')}")
            name = tag.get("name", "")
            name_en = tag.get("name_en", "")
            description = tag.get("description", "")
            examples = json.dumps(tag.get("examples", [])) if tag.get("examples") else None
            parent_id = tag.get("parent")
            
            await db.execute(
                """INSERT OR REPLACE INTO script_tags 
                   (id, category, name, name_en, description, examples, parent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (tag_id, category, name, name_en, description, examples, parent_id)
            )
            tag_count += 1
    
    print(f"Loaded {tag_count} tags from config")


async def _load_seeds_from_files():
    import os
    import glob
    
    seeds_dir = os.path.join(os.path.dirname(__file__), "..", "..", "config", "script_seeds")
    
    if not os.path.exists(seeds_dir):
        print("Warning: script_seeds directory not found, skipping seed import")
        return
    
    seed_files = glob.glob(os.path.join(seeds_dir, "*.json"))
    total_seeds = 0
    
    for seed_file in seed_files:
        with open(seed_file, "r", encoding="utf-8") as f:
            seeds = json.load(f)
        
        for seed in seeds:
            script_id = seed.get("id", f"script_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{total_seeds}")
            
            await db.execute(
                """INSERT OR REPLACE INTO script_library 
                   (id, title, title_en, summary, emotion_tones, relation_types, 
                    contrast_types, era, gender_target, character_gender, profession,
                    length, age_rating, contrast_surface, contrast_truth, contrast_hook,
                    script_seed, status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    script_id,
                    seed.get("title"),
                    seed.get("title_en"),
                    seed.get("summary"),
                    json.dumps(seed.get("emotion_tones", [])),
                    json.dumps(seed.get("relation_types", [])),
                    json.dumps(seed.get("contrast_types", [])),
                    seed.get("era"),
                    seed.get("gender_target"),
                    seed.get("character_gender"),
                    seed.get("profession"),
                    seed.get("length"),
                    seed.get("age_rating"),
                    seed.get("contrast_surface"),
                    seed.get("contrast_truth"),
                    seed.get("contrast_hook"),
                    json.dumps(seed.get("script_seed", {})),
                    "published",
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat()
                )
            )
            total_seeds += 1
    
    print(f"Loaded {total_seeds} script seeds from {len(seed_files)} files")


if __name__ == "__main__":
    asyncio.run(migrate())
