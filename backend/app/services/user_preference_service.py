import json
import logging
import uuid
from collections import Counter
from datetime import datetime
from typing import Optional

from app.core.database import db

logger = logging.getLogger(__name__)

INTERACTION_WEIGHTS = {
    "favorite": 3.0,
    "chat_heavy": 2.0,
    "chat_light": 1.5,
    "view_long": 1.0,
    "view_short": 0.3,
    "created": 1.5,
}

CHAT_HEAVY_THRESHOLD = 10
VIEW_LONG_SECONDS = 30
MIN_INTERACTIONS_FOR_PROFILE = 3


class UserPreferenceService:
    _instance = None

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls) -> "UserPreferenceService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def record_view(
        self,
        user_id: str,
        character_id: str,
        view_duration_seconds: int = 0,
    ) -> str:
        view_id = f"view_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()

        await db.execute(
            """INSERT INTO character_views (id, user_id, character_id, view_duration_seconds, viewed_at)
               VALUES (?, ?, ?, ?, ?)""",
            (view_id, user_id, character_id, view_duration_seconds, now),
        )

        await self._update_profile_incremental(user_id, character_id, "view_long" if view_duration_seconds >= VIEW_LONG_SECONDS else "view_short")

        return view_id

    async def add_favorite(self, user_id: str, character_id: str) -> dict:
        existing = await db.execute(
            "SELECT id FROM character_favorites WHERE user_id = ? AND character_id = ?",
            (user_id, character_id),
            fetch=True,
        )
        if existing:
            return {"id": existing["id"], "status": "already_favorited"}

        fav_id = f"fav_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()

        await db.execute(
            """INSERT INTO character_favorites (id, user_id, character_id, created_at)
               VALUES (?, ?, ?, ?)""",
            (fav_id, user_id, character_id, now),
        )

        await self._update_profile_incremental(user_id, character_id, "favorite")

        return {"id": fav_id, "status": "favorited"}

    async def remove_favorite(self, user_id: str, character_id: str) -> bool:
        result = await db.execute(
            "DELETE FROM character_favorites WHERE user_id = ? AND character_id = ?",
            (user_id, character_id),
        )
        return result is not None

    async def get_favorites(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict], int]:
        count_row = await db.execute(
            "SELECT COUNT(*) as cnt FROM character_favorites WHERE user_id = ?",
            (user_id,),
            fetch=True,
        )
        total = count_row["cnt"] if count_row else 0

        offset = (page - 1) * page_size
        rows = await db.execute(
            """SELECT f.id, f.character_id, f.created_at,
                      c.name, c.first_name, c.avatar_url, c.personality_tags,
                      c.description, c.top_category
               FROM character_favorites f
               LEFT JOIN characters c ON f.character_id = c.id
               WHERE f.user_id = ?
               ORDER BY f.created_at DESC
               LIMIT ? OFFSET ?""",
            (user_id, page_size, offset),
            fetch_all=True,
        )

        favorites = []
        for row in rows:
            fav = dict(row)
            if fav.get("personality_tags") and isinstance(fav["personality_tags"], str):
                try:
                    fav["personality_tags"] = json.loads(fav["personality_tags"])
                except (json.JSONDecodeError, TypeError):
                    fav["personality_tags"] = []
            favorites.append(fav)

        return favorites, total

    async def is_favorited(self, user_id: str, character_id: str) -> bool:
        row = await db.execute(
            "SELECT id FROM character_favorites WHERE user_id = ? AND character_id = ?",
            (user_id, character_id),
            fetch=True,
        )
        return row is not None

    async def build_user_profile(self, user_id: str) -> Optional[dict]:
        character_weights: dict[str, float] = {}

        fav_rows = await db.execute(
            "SELECT character_id FROM character_favorites WHERE user_id = ?",
            (user_id,),
            fetch_all=True,
        )
        for row in fav_rows:
            cid = row["character_id"]
            character_weights[cid] = character_weights.get(cid, 0) + INTERACTION_WEIGHTS["favorite"]

        view_rows = await db.execute(
            "SELECT character_id, view_duration_seconds FROM character_views WHERE user_id = ?",
            (user_id,),
            fetch_all=True,
        )
        for row in view_rows:
            cid = row["character_id"]
            weight = INTERACTION_WEIGHTS["view_long"] if row["view_duration_seconds"] >= VIEW_LONG_SECONDS else INTERACTION_WEIGHTS["view_short"]
            character_weights[cid] = character_weights.get(cid, 0) + weight

        if len(character_weights) < MIN_INTERACTIONS_FOR_PROFILE:
            return None

        character_ids = list(character_weights.keys())
        placeholders = ",".join(["?" for _ in character_ids])
        char_rows = await db.execute(
            f"SELECT id, ethnicity, nationality, occupation, personality_tags, age FROM characters WHERE id IN ({placeholders})",
            tuple(character_ids),
            fetch_all=True,
        )

        character_map = {}
        for row in char_rows:
            char_dict = dict(row)
            if char_dict.get("personality_tags") and isinstance(char_dict["personality_tags"], str):
                try:
                    char_dict["personality_tags"] = json.loads(char_dict["personality_tags"])
                except (json.JSONDecodeError, TypeError):
                    char_dict["personality_tags"] = []
            character_map[char_dict["id"]] = char_dict

        ethnicity_counter: Counter = Counter()
        nationality_counter: Counter = Counter()
        occupation_counter: Counter = Counter()
        personality_counter: Counter = Counter()
        ages: list[int] = []

        for cid, weight in character_weights.items():
            char = character_map.get(cid)
            if not char:
                continue

            if char.get("ethnicity"):
                ethnicity_counter[char["ethnicity"]] += weight
            if char.get("nationality"):
                nationality_counter[char["nationality"]] += weight
            if char.get("occupation"):
                occupation_counter[char["occupation"]] += weight
            if char.get("personality_tags"):
                for tag in char["personality_tags"]:
                    personality_counter[tag] += weight
            if char.get("age"):
                ages.append(char["age"])

        age_range = None
        if ages:
            age_range = {"min": min(ages), "max": max(ages)}

        profile = {
            "preferred_ethnicities": normalize(ethnicity_counter),
            "preferred_nationalities": normalize(nationality_counter),
            "preferred_occupations": normalize(occupation_counter),
            "preferred_personality_tags": normalize(personality_counter),
            "preferred_age_range": age_range,
            "preferred_appearance": {},
            "total_interactions": len(character_weights),
            "last_updated": datetime.utcnow().isoformat(),
        }

        await self._save_profile(user_id, profile)

        return profile

    async def get_preference_vector(self, user_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM user_preference_profiles WHERE user_id = ?",
            (user_id,),
            fetch=True,
        )
        if not row:
            profile = await self.build_user_profile(user_id)
            return profile

        profile = {}
        json_fields = [
            "preferred_ethnicities",
            "preferred_nationalities",
            "preferred_occupations",
            "preferred_personality_tags",
            "preferred_age_range",
            "preferred_appearance",
        ]
        for field in json_fields:
            val = row.get(field)
            if val and isinstance(val, str):
                try:
                    profile[field] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    profile[field] = {}
            elif val:
                profile[field] = val
            else:
                profile[field] = {}

        profile["total_interactions"] = row.get("total_interactions", 0)
        profile["last_updated"] = row.get("last_updated")

        return profile

    async def _update_profile_incremental(
        self, user_id: str, character_id: str, interaction_type: str
    ):
        row = await db.execute(
            "SELECT total_interactions FROM user_preference_profiles WHERE user_id = ?",
            (user_id,),
            fetch=True,
        )
        current = row["total_interactions"] if row else 0
        new_count = current + 1

        if new_count % 5 == 0 or new_count < MIN_INTERACTIONS_FOR_PROFILE:
            await self.build_user_profile(user_id)

    async def _save_profile(self, user_id: str, profile: dict):
        now = datetime.utcnow().isoformat()

        await db.execute(
            """INSERT INTO user_preference_profiles
               (user_id, preferred_ethnicities, preferred_nationalities,
                preferred_occupations, preferred_personality_tags,
                preferred_age_range, preferred_appearance,
                total_interactions, last_updated)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                preferred_ethnicities = excluded.preferred_ethnicities,
                preferred_nationalities = excluded.preferred_nationalities,
                preferred_occupations = excluded.preferred_occupations,
                preferred_personality_tags = excluded.preferred_personality_tags,
                preferred_age_range = excluded.preferred_age_range,
                preferred_appearance = excluded.preferred_appearance,
                total_interactions = excluded.total_interactions,
                last_updated = excluded.last_updated
            """,
            (
                user_id,
                json.dumps(profile.get("preferred_ethnicities", {})),
                json.dumps(profile.get("preferred_nationalities", {})),
                json.dumps(profile.get("preferred_occupations", {})),
                json.dumps(profile.get("preferred_personality_tags", {})),
                json.dumps(profile.get("preferred_age_range")),
                json.dumps(profile.get("preferred_appearance", {})),
                profile.get("total_interactions", 0),
                now,
            ),
        )


user_preference_service = UserPreferenceService()
