"""
Migrate script_library: remove hardcoded character names from script_seed and full_script.
Replaces character.name with placeholder "{{character_name}}" so scripts can be reused across characters.

Run: python -m app.migrations.migrate_script_library_dynamic_names
"""
import asyncio
import json
import os
import sys
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import db


def _replace_name_in_obj(obj, name: str):
    if isinstance(obj, str):
        return obj.replace(name, "{{character_name}}")
    if isinstance(obj, dict):
        return {k: (_replace_name_in_obj(v, name) if k != "name" else v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_replace_name_in_obj(item, name) for item in obj]
    return obj


async def migrate():
    print("Starting script_library dynamic names migration...")
    await db.connect()

    rows = await db.execute(
        "SELECT id, script_seed, full_script FROM script_library",
        fetch_all=True
    )

    if not rows:
        print("No scripts found, nothing to migrate.")
        return

    updated = 0
    for row in rows:
        script_id = row["id"]
        seed_json = row.get("script_seed")
        full_json = row.get("full_script")
        changed = False

        character_name = None

        if seed_json:
            try:
                seed = json.loads(seed_json) if isinstance(seed_json, str) else seed_json
                char_info = seed.get("character", {})
                character_name = char_info.get("name")

                if character_name:
                    seed["character"]["name"] = "{{character_name}}"
                    new_seed_json = json.dumps(seed, ensure_ascii=False)
                    if new_seed_json != seed_json:
                        seed_json = new_seed_json
                        changed = True
            except (json.JSONDecodeError, TypeError):
                print(f"  Warning: could not parse script_seed for {script_id}")

        if full_json and character_name:
            try:
                full = json.loads(full_json) if isinstance(full_json, str) else full_json
                new_full = _replace_name_in_obj(full, character_name)
                new_full_json = json.dumps(new_full, ensure_ascii=False)
                if new_full_json != full_json:
                    full_json = new_full_json
                    changed = True
            except (json.JSONDecodeError, TypeError):
                print(f"  Warning: could not parse full_script for {script_id}")

        if changed:
            await db.execute(
                "UPDATE script_library SET script_seed = ?, full_script = ?, updated_at = ? WHERE id = ?",
                (seed_json, full_json, datetime.utcnow().isoformat(), script_id)
            )
            updated += 1

    print(f"Migration complete. Updated {updated}/{len(rows)} scripts.")


if __name__ == "__main__":
    asyncio.run(migrate())
