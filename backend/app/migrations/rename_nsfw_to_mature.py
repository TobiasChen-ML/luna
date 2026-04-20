"""
Rename legacy nsfw_* columns to mature_* in characters table,
and collapse script_library.age_rating value 'r18' into 'mature'.

Safe to run multiple times (idempotent):
- Skips column rename if mature_* already exists.
- Only updates rows where age_rating = 'r18'.
"""
import asyncio
import logging
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

COLUMN_RENAMES = [
    ("nsfw_image_url", "mature_image_url"),
    ("nsfw_cover_url", "mature_cover_url"),
    ("nsfw_video_url", "mature_video_url"),
]


async def run_migration(db_path: str = "roxy.db") -> None:
    async with aiosqlite.connect(db_path) as conn:
        # ── 1. Rename columns on characters table ────────────────────────────
        cursor = await conn.execute("PRAGMA table_info(characters)")
        existing = {row[1] async for row in cursor}

        for old_name, new_name in COLUMN_RENAMES:
            if new_name in existing:
                logger.info(f"Column already renamed: characters.{new_name}")
                continue
            if old_name in existing:
                await conn.execute(
                    f"ALTER TABLE characters RENAME COLUMN {old_name} TO {new_name}"
                )
                logger.info(f"Renamed: characters.{old_name} → characters.{new_name}")
            else:
                await conn.execute(
                    f"ALTER TABLE characters ADD COLUMN {new_name} TEXT"
                )
                logger.info(f"Added missing column: characters.{new_name}")

        # ── 2. Collapse script_library.age_rating 'r18' → 'mature' ───────────
        cursor = await conn.execute(
            "SELECT COUNT(*) FROM script_library WHERE age_rating = 'r18'"
        )
        row = await cursor.fetchone()
        r18_count = row[0] if row else 0

        if r18_count:
            await conn.execute(
                "UPDATE script_library SET age_rating = 'mature' WHERE age_rating = 'r18'"
            )
            logger.info(f"Updated {r18_count} script_library rows: age_rating 'r18' → 'mature'")
        else:
            logger.info("No script_library rows with age_rating='r18' to update")

        # ── 3. Rename script_library IDs with _r18 suffix → _mature ─────────
        cursor = await conn.execute(
            "SELECT id FROM script_library WHERE id LIKE '%\\_r18' ESCAPE '\\'"
        )
        ids_to_rename = [r[0] async for r in cursor]
        for old_id in ids_to_rename:
            new_id = old_id[:-4] + "_mature"
            # Skip if target already exists
            exists = await conn.execute(
                "SELECT 1 FROM script_library WHERE id = ?", (new_id,)
            )
            if await exists.fetchone():
                logger.warning(f"Skip rename {old_id}: target {new_id} already exists")
                continue
            await conn.execute(
                "UPDATE script_library SET id = ? WHERE id = ?", (new_id, old_id)
            )
            logger.info(f"Renamed script_library.id: {old_id} → {new_id}")

        await conn.commit()

    logger.info("Migration rename_nsfw_to_mature complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_path = Path(__file__).parent.parent.parent / "roxy.db"
    asyncio.run(run_migration(str(db_path)))
