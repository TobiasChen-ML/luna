"""Add mature_image_url, mature_cover_url, mature_video_url to characters table."""
import asyncio
import logging
import aiosqlite
from pathlib import Path

logger = logging.getLogger(__name__)

NEW_COLUMNS = [
    ("mature_image_url", "TEXT"),
    ("mature_cover_url", "TEXT"),
    ("mature_video_url", "TEXT"),
]


async def run_migration(db_path: str = "roxy.db") -> None:
    async with aiosqlite.connect(db_path) as conn:
        cursor = await conn.execute("PRAGMA table_info(characters)")
        existing = {row[1] async for row in cursor}

        for col_name, col_type in NEW_COLUMNS:
            if col_name not in existing:
                await conn.execute(
                    f"ALTER TABLE characters ADD COLUMN {col_name} {col_type}"
                )
                logger.info(f"Added column: characters.{col_name}")
            else:
                logger.info(f"Column already exists: characters.{col_name}")

        await conn.commit()
    logger.info("Migration add_mature_media_fields complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_path = Path(__file__).parent.parent.parent / "roxy.db"
    asyncio.run(run_migration(str(db_path)))
