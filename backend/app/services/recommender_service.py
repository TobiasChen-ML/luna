import json
import logging
from typing import Optional

from app.core.database import db
from app.services.user_preference_service import user_preference_service

logger = logging.getLogger(__name__)

POPULARITY_WEIGHT = 0.4
PERSONALIZATION_WEIGHT = 0.6

AFFINITY_WEIGHTS = {
    "ethnicity": 0.15,
    "nationality": 0.15,
    "occupation": 0.25,
    "personality_tags": 0.25,
    "age": 0.10,
    "appearance": 0.10,
}


class RecommenderService:
    _instance = None

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls) -> "RecommenderService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def compute_affinity_score(
        self, character: dict, user_profile: dict
    ) -> float:
        score = 0.0

        pref_ethnicities = user_profile.get("preferred_ethnicities", {})
        if pref_ethnicities and character.get("ethnicity"):
            ethnicity_score = pref_ethnicities.get(character["ethnicity"], 0.0)
            score += AFFINITY_WEIGHTS["ethnicity"] * ethnicity_score

        pref_nationalities = user_profile.get("preferred_nationalities", {})
        if pref_nationalities and character.get("nationality"):
            nationality_score = pref_nationalities.get(character["nationality"], 0.0)
            score += AFFINITY_WEIGHTS["nationality"] * nationality_score

        pref_occupations = user_profile.get("preferred_occupations", {})
        if pref_occupations and character.get("occupation"):
            occupation_score = pref_occupations.get(character["occupation"], 0.0)
            score += AFFINITY_WEIGHTS["occupation"] * occupation_score

        pref_personality = user_profile.get("preferred_personality_tags", {})
        if pref_personality:
            char_tags = character.get("personality_tags", [])
            if isinstance(char_tags, str):
                try:
                    char_tags = json.loads(char_tags)
                except (json.JSONDecodeError, TypeError):
                    char_tags = []

            if char_tags:
                tag_scores = [pref_personality.get(t, 0.0) for t in char_tags if t in pref_personality]
                if tag_scores:
                    avg_tag_score = sum(tag_scores) / len(tag_scores)
                    score += AFFINITY_WEIGHTS["personality_tags"] * avg_tag_score

        pref_age_range = user_profile.get("preferred_age_range")
        if pref_age_range and character.get("age"):
            char_age = character["age"]
            min_age = pref_age_range.get("min", 18)
            max_age = pref_age_range.get("max", 35)
            if min_age <= char_age <= max_age:
                age_score = 1.0
            elif char_age < min_age:
                age_score = max(0, 1.0 - (min_age - char_age) / 10.0)
            else:
                age_score = max(0, 1.0 - (char_age - max_age) / 10.0)
            score += AFFINITY_WEIGHTS["age"] * age_score

        return score

    async def personalize_rank(
        self,
        user_id: str,
        characters: list[dict],
        popularity_weight: float = POPULARITY_WEIGHT,
        personalization_weight: float = PERSONALIZATION_WEIGHT,
    ) -> list[dict]:
        user_profile = await user_preference_service.get_preference_vector(user_id)

        if not user_profile or not user_profile.get("preferred_personality_tags"):
            return characters

        max_popularity = max(
            (c.get("popularity_score", 0) for c in characters), default=1.0
        ) or 1.0

        for char in characters:
            popularity_norm = char.get("popularity_score", 0) / max_popularity
            affinity = self.compute_affinity_score(char, user_profile)

            char["_personalization_score"] = affinity
            char["_final_rank_score"] = (
                popularity_weight * popularity_norm
                + personalization_weight * affinity
            )

        sorted_chars = sorted(
            characters, key=lambda c: c.get("_final_rank_score", 0), reverse=True
        )

        for char in sorted_chars:
            char.pop("_personalization_score", None)
            char.pop("_final_rank_score", None)

        return sorted_chars

    async def get_personalized_discover(
        self,
        user_id: str,
        top_category: str = "girls",
        filter_tag: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 24,
        offset: int = 0,
    ) -> list[dict]:
        from app.services.character_service import character_service

        fetch_limit = min(limit * 5, 200)

        characters = await character_service.discover_characters(
            top_category=top_category,
            filter_tag=filter_tag,
            search=search,
            limit=fetch_limit,
            offset=0,
        )

        if not characters:
            return []

        ranked = await self.personalize_rank(user_id, characters)

        return ranked[offset : offset + limit]


recommender_service = RecommenderService()
