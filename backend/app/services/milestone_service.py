"""
Milestone Service

Writes entries to the relationship_milestones table at key user–character moments:
- Relationship stage-up
- Story created from session
- First message (day 1)
- 7-day / 30-day / 100-day streaks
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from app.core.database import db

logger = logging.getLogger(__name__)

MILESTONE_TYPES = frozenset(
    ["stage_up", "story_created", "first_message", "streak_7day", "streak_30day", "streak_100day"]
)


async def write_milestone(
    user_id: str,
    character_id: str,
    milestone_type: str,
    description: Optional[str] = None,
) -> None:
    if milestone_type not in MILESTONE_TYPES:
        logger.warning(f"Unknown milestone_type: {milestone_type}")
        return
    try:
        await db.execute(
            """
            INSERT INTO relationship_milestones
                (id, user_id, character_id, milestone_type, description, occurred_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                user_id,
                character_id,
                milestone_type,
                description,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        logger.debug(f"Milestone {milestone_type} written for {user_id}/{character_id}")
    except Exception as e:
        logger.warning(f"Failed to write milestone {milestone_type}: {e}")


async def check_and_write_streak_milestones(
    user_id: str,
    character_id: str,
) -> None:
    """Check how many distinct days the user has chatted with the character and write streak milestones."""
    try:
        row = await db.execute(
            """
            SELECT COUNT(DISTINCT date(created_at)) AS day_count
            FROM chat_messages
            WHERE user_id = ? AND character_id = ? AND role = 'user'
            """,
            (user_id, character_id),
            fetch=True,
        )
        day_count = (row or {}).get("day_count", 0)

        if day_count >= 1:
            existing_first = await db.execute(
                """
                SELECT id FROM relationship_milestones
                WHERE user_id = ? AND character_id = ? AND milestone_type = 'first_message'
                LIMIT 1
                """,
                (user_id, character_id),
                fetch=True,
            )
            if not existing_first:
                await write_milestone(
                    user_id,
                    character_id,
                    "first_message",
                    "First conversation",
                )

        for days, milestone in [(100, "streak_100day"), (30, "streak_30day"), (7, "streak_7day")]:
            if day_count >= days:
                existing = await db.execute(
                    """
                    SELECT id FROM relationship_milestones
                    WHERE user_id = ? AND character_id = ? AND milestone_type = ?
                    LIMIT 1
                    """,
                    (user_id, character_id, milestone),
                    fetch=True,
                )
                if not existing:
                    await write_milestone(
                        user_id,
                        character_id,
                        milestone,
                        f"{days} days of conversations",
                    )
                break
    except Exception as e:
        logger.warning(f"Streak milestone check failed: {e}")
