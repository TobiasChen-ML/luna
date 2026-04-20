"""
Import script library data from config files
Run this after the migration to populate the database
"""
import asyncio
import json
import os
import glob
from datetime import datetime
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import db


async def import_data():
    print("Starting data import...")
    
    await db.connect()
    
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    project_root = os.path.dirname(backend_dir)
    config_dir = os.path.join(project_root, "config")
    
    await import_tags(config_dir)
    await import_seeds(config_dir)
    
    print("Data import completed!")


async def import_tags(config_dir: str):
    tags_file = os.path.join(config_dir, "script_tags.json")
    
    if not os.path.exists(tags_file):
        print(f"Warning: {tags_file} not found")
        return
    
    print(f"Loading tags from {tags_file}")
    
    with open(tags_file, "r", encoding="utf-8") as f:
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
    
    print(f"Imported {tag_count} tags")


async def import_seeds(config_dir: str):
    seeds_dir = os.path.join(config_dir, "script_seeds")
    
    if not os.path.exists(seeds_dir):
        print(f"Warning: {seeds_dir} not found")
        return
    
    print(f"Loading seeds from {seeds_dir}")
    
    seed_files = glob.glob(os.path.join(seeds_dir, "*.json"))
    total_seeds = 0
    
    for seed_file in seed_files:
        print(f"Processing {os.path.basename(seed_file)}")
        
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
    
    print(f"Imported {total_seeds} script seeds from {len(seed_files)} files")


if __name__ == "__main__":
    asyncio.run(import_data())
