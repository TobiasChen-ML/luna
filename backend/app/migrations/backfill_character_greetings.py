"""
Backfill empty character greetings for existing records.

Rules:
1. Keep existing non-empty greeting unchanged.
2. Prefer script-driven opening from character_script_bindings + script_library.
3. Fallback to personality/occupation/backstory-based opening.

Usage:
    python -m app.migrations.backfill_character_greetings
    python -m app.migrations.backfill_character_greetings --dry-run
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

import aiosqlite

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _safe_parse_json(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {}
    return {}


def _compose_script_opening(
    *,
    character_name: str,
    personality: str,
    opening_line: str,
    opening_scene: str,
    world_setting: str,
    user_role: str,
) -> str:
    base = opening_line.strip()
    if not base:
        if opening_scene:
            base = f"*{opening_scene}*"
        elif world_setting:
            base = f"We're in {world_setting}."
        elif personality:
            base = f"Hi, I'm {character_name}. {personality}"
        else:
            base = f"Hi, I'm {character_name}."

    if user_role:
        starter = (
            f"You are {user_role} in this story. "
            "Start by telling me your first move in this scene."
        )
    elif opening_scene or world_setting:
        starter = "Start by telling me what you do first in this scene."
    else:
        starter = "Start by telling me what kind of moment you want to have."

    return f"{base}\n\n{starter}"


def _build_default_opening(character: dict[str, Any]) -> str:
    name = (
        str(character.get("first_name") or "").strip()
        or str(character.get("name") or "").strip()
        or "AI"
    )
    personality = str(character.get("personality_summary") or "").strip()
    occupation = str(character.get("occupation") or "").strip()
    backstory = str(character.get("backstory") or "").strip()

    intro = f"Hi, I'm {name}."
    if personality:
        intro = f"{intro} {personality}"
    elif occupation:
        intro = f"{intro} I'm a {occupation}."
    elif backstory:
        intro = f"{intro} {backstory[:120].rstrip()}"

    return (
        f"{intro} "
        "Tell me what mood you're in, or start with: "
        f"\"Hey {name}, what kind of moment are we in right now?\""
    )


async def _pick_script_library_opening(
    db: aiosqlite.Connection, character: dict[str, Any]
) -> Optional[str]:
    character_id = str(character.get("id") or "").strip()
    if not character_id:
        return None

    row = await db.execute(
        """
        SELECT s.summary, s.full_script
        FROM character_script_bindings b
        JOIN script_library s ON s.id = b.script_id
        WHERE b.character_id = ?
          AND b.is_active = 1
          AND s.status = 'published'
        ORDER BY b.weight DESC, b.updated_at DESC
        LIMIT 1
        """,
        (character_id,),
        fetch=True,
    )
    if not row:
        return None

    name = (
        str(character.get("first_name") or "").strip()
        or str(character.get("name") or "").strip()
        or "AI"
    )
    personality = str(character.get("personality_summary") or "").strip()
    world_setting = str(row.get("summary") or "").strip()
    full_script = _safe_parse_json(row.get("full_script"))

    opening_line = str(
        full_script.get("opening_line")
        or full_script.get("opening")
        or full_script.get("opening_message")
        or ""
    ).strip()
    opening_scene = str(full_script.get("opening_scene") or full_script.get("prologue") or "").strip()

    if not (opening_line or opening_scene or world_setting):
        return None

    return _compose_script_opening(
        character_name=name,
        personality=personality,
        opening_line=opening_line,
        opening_scene=opening_scene,
        world_setting=world_setting,
        user_role="",
    )


async def _fetch_target_characters(db: aiosqlite.Connection) -> list[dict[str, Any]]:
    rows = await db.execute(
        """
        SELECT id, name, first_name, personality_summary, occupation, backstory, greeting
        FROM characters
        WHERE greeting IS NULL OR TRIM(greeting) = ''
        ORDER BY created_at ASC
        """,
        fetch_all=True,
    )
    return [dict(row) for row in (rows or [])]


async def migrate(dry_run: bool = False) -> None:
    from app.core.config import settings
    from app.core.database import db as db_service

    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    logger.info(f"Starting greeting backfill on {db_path} (dry_run={dry_run})")

    targets = await _fetch_target_characters(db_service)
    if not targets:
        logger.info("No characters need backfill. Done.")
        return

    updated = 0
    script_based = 0
    fallback_based = 0

    for character in targets:
        greeting = await _pick_script_library_opening(db_service, character)
        if greeting:
            script_based += 1
        else:
            greeting = _build_default_opening(character)
            fallback_based += 1

        if not dry_run:
            await db_service.execute(
                "UPDATE characters SET greeting = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (greeting, character["id"]),
            )
        updated += 1

    if not dry_run:
        await db_service.execute("SELECT 1")

    logger.info(
        "Greeting backfill finished. updated=%s script_based=%s fallback_based=%s",
        updated,
        script_based,
        fallback_based,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill empty character greetings.")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not write to DB.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(migrate(dry_run=args.dry_run))
