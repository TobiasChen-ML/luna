"""
Database migration: add LoRA prompt-template columns to lora_presets table.

Usage:
    python -m app.migrations.add_lora_prompt_templates
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _add_column(sql: str, exists_hint: str) -> None:
    from app.core.database import db

    try:
        await db.execute(sql)
        logger.info("Column added: %s", exists_hint)
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            logger.info("Column already exists, skipping: %s", exists_hint)
        else:
            raise


async def migrate() -> None:
    logger.info("Adding LoRA prompt-template columns to lora_presets...")
    await _add_column(
        "ALTER TABLE lora_presets ADD COLUMN example_prompt TEXT NOT NULL DEFAULT ''",
        "example_prompt",
    )
    await _add_column(
        "ALTER TABLE lora_presets ADD COLUMN example_negative_prompt TEXT NOT NULL DEFAULT ''",
        "example_negative_prompt",
    )
    await _add_column(
        "ALTER TABLE lora_presets ADD COLUMN prompt_template_mode TEXT NOT NULL DEFAULT 'append_trigger'",
        "prompt_template_mode",
    )
    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
