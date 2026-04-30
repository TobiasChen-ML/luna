import uuid
from datetime import datetime, timedelta
from typing import Any

from app.core.database import db


VIRTUAL_COMMENT_AUTHORS = [
    "Maya",
    "Alex",
    "Sofia",
    "Jordan",
    "Lena",
    "Noah",
    "Iris",
    "Mika",
    "Riley",
    "Evan",
]

VIRTUAL_COMMENT_TEXTS = [
    "The preview feels natural and easy to talk to.",
    "I like the mood here. It makes the first message feel simple.",
    "The personality comes through better than I expected.",
    "This one has a calm, warm energy.",
    "The intro makes me want to start a chat.",
    "The scene and expression work well together.",
    "This character feels good for a slower story chat.",
    "The visual style is polished without feeling too staged.",
    "I saved this one for later.",
    "The preview gives just enough detail to be interesting.",
    "Feels like a good match for a relaxed conversation.",
    "The background story makes the character easier to approach.",
]


def _seeded_number(seed: str, base: int, mod: int) -> int:
    value = 0
    for char in seed:
        value = (value * 31 + ord(char)) % 100000
    return base + (value % mod)


class DiscoverCommentService:
    def _build_virtual_comments(self, character_id: str) -> list[dict[str, Any]]:
        count = _seeded_number(f"{character_id}:virtual-comment-count", 6, 7)
        now = datetime.utcnow()

        comments: list[dict[str, Any]] = []
        for index in range(count):
            seed = f"{character_id}:virtual-comment:{index}"
            author = VIRTUAL_COMMENT_AUTHORS[_seeded_number(f"{seed}:author", 0, len(VIRTUAL_COMMENT_AUTHORS))]
            text = VIRTUAL_COMMENT_TEXTS[_seeded_number(f"{seed}:text", 0, len(VIRTUAL_COMMENT_TEXTS))]
            minutes_ago = _seeded_number(f"{seed}:time", 3, 60 * 48)
            comments.append(
                {
                    "id": f"virtual_{character_id}_{index}",
                    "character_id": character_id,
                    "author": author,
                    "text": text,
                    "likes": _seeded_number(f"{seed}:likes", 2, 180),
                    "created_at": (now - timedelta(minutes=minutes_ago)).isoformat(),
                    "is_virtual": True,
                }
            )

        return comments

    async def _ensure_table(self) -> None:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS discover_comments (
                id TEXT PRIMARY KEY,
                character_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                author_name TEXT NOT NULL,
                text TEXT NOT NULL,
                likes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_discover_comments_character ON discover_comments(character_id, created_at DESC)"
        )

    @staticmethod
    def _row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "character_id": row["character_id"],
            "author": row["author_name"],
            "text": row["text"],
            "likes": row.get("likes") or 0,
            "created_at": row["created_at"],
            "is_virtual": False,
        }

    async def list_comments(self, character_id: str) -> list[dict[str, Any]]:
        await self._ensure_table()
        rows = await db.execute(
            """
            SELECT id, character_id, author_name, text, likes, created_at
            FROM discover_comments
            WHERE character_id = ?
            ORDER BY created_at DESC
            """,
            (character_id,),
            fetch_all=True,
        )
        real_comments = [self._row_to_dict(row) for row in rows]
        return real_comments + self._build_virtual_comments(character_id)

    async def create_comment(
        self,
        character_id: str,
        user_id: str,
        author_name: str,
        text: str,
    ) -> dict[str, Any]:
        await self._ensure_table()
        comment_id = f"disc_comment_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        cleaned_author = author_name.strip() or "User"
        cleaned_text = text.strip()

        await db.execute(
            """
            INSERT INTO discover_comments (id, character_id, user_id, author_name, text, likes, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (comment_id, character_id, user_id, cleaned_author, cleaned_text, now),
        )

        return {
            "id": comment_id,
            "character_id": character_id,
            "author": cleaned_author,
            "text": cleaned_text,
            "likes": 0,
            "created_at": now,
            "is_virtual": False,
        }

    async def count_by_character_ids(self, character_ids: list[str]) -> dict[str, int]:
        if not character_ids:
            return {}

        await self._ensure_table()
        placeholders = ", ".join("?" for _ in character_ids)
        rows = await db.execute(
            f"""
            SELECT character_id, COUNT(*) AS count
            FROM discover_comments
            WHERE character_id IN ({placeholders})
            GROUP BY character_id
            """,
            tuple(character_ids),
            fetch_all=True,
        )
        counts = {row["character_id"]: int(row["count"]) for row in rows}
        return {
            character_id: counts.get(character_id, 0) + len(self._build_virtual_comments(character_id))
            for character_id in character_ids
        }


discover_comment_service = DiscoverCommentService()
