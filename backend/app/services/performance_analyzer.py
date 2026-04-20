import json
import logging
import random
import uuid
from collections import Counter
from datetime import datetime
from typing import Optional

from app.core.database import db
from app.models.character import OCCUPATION_TEMPLATES, ETHNICITY_IMAGE_STYLES, NATIONALITY_CONFIGS

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    _instance = None

    def __init__(self):
        pass

    @classmethod
    def get_instance(cls) -> "PerformanceAnalyzer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def analyze_top_performers(self, days: int = 30) -> dict:
        rows = await db.execute(
            f"""SELECT c.id, c.occupation, c.ethnicity, c.nationality, c.age,
                      c.personality_tags, c.top_category,
                      COALESCE(SUM(cp.views), 0) as total_views,
                      COALESCE(SUM(cp.clicks), 0) as total_clicks,
                      COALESCE(SUM(cp.chats_started), 0) as total_chats,
                      COALESCE(AVG(cp.avg_messages_per_chat), 0) as avg_messages
               FROM characters c
               LEFT JOIN character_performance cp ON c.id = cp.character_id
               WHERE cp.date >= date('now', '-{days} days')
               GROUP BY c.id
               HAVING total_views > 0
               ORDER BY total_chats DESC, total_clicks DESC
               LIMIT 50""",
            fetch_all=True,
        )

        if not rows:
            return {"top_occupations": {}, "top_ethnicities": {}, "top_personality_tags": {}}

        occupation_counter: Counter = Counter()
        ethnicity_counter: Counter = Counter()
        personality_counter: Counter = Counter()

        for row in rows:
            char = dict(row)
            weight = char.get("total_chats", 0) * 2 + char.get("total_clicks", 0)

            if char.get("occupation"):
                occupation_counter[char["occupation"]] += weight
            if char.get("ethnicity"):
                ethnicity_counter[char["ethnicity"]] += weight
            if char.get("personality_tags"):
                try:
                    tags = json.loads(char["personality_tags"]) if isinstance(char["personality_tags"], str) else char["personality_tags"]
                    for tag in tags:
                        personality_counter[tag] += weight
                except (json.JSONDecodeError, TypeError):
                    pass

        def normalize(counter: Counter) -> dict:
            if not counter:
                return {}
            max_val = max(counter.values())
            if max_val == 0:
                return {}
            return {k: round(v / max_val, 3) for k, v in counter.most_common(20)}

        return {
            "top_occupations": normalize(occupation_counter),
            "top_ethnicities": normalize(ethnicity_counter),
            "top_personality_tags": normalize(personality_counter),
        }

    async def update_generation_weights(self, analysis: dict) -> int:
        now = datetime.utcnow().isoformat()
        updated = 0

        for category, values in analysis.items():
            if not values:
                continue
            for attr_value, weight in values.items():
                weight_id = f"gw_{uuid.uuid4().hex[:12]}"

                await db.execute(
                    """INSERT OR REPLACE INTO generation_weights
                       (id, category, attribute_key, attribute_value, weight, source, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (weight_id, category, category.rstrip("s"), attr_value, weight, "performance", now),
                )
                updated += 1

        logger.info(f"Updated {updated} generation weights from performance analysis")
        return updated

    async def get_weighted_choice(self, category: str, options: list[str], default_weight: float = 1.0) -> str:
        if not options:
            return ""

        rows = await db.execute(
            f"""SELECT attribute_value, weight FROM generation_weights
                WHERE category = ? AND attribute_value IN ({','.join(['?' for _ in options])})""",
            (category, *options),
            fetch_all=True,
        )

        weight_map = {row["attribute_value"]: row["weight"] for row in rows} if rows else {}

        weights = [weight_map.get(opt, default_weight) for opt in options]
        total = sum(weights)
        if total == 0:
            return random.choice(options)

        r = random.uniform(0, total)
        cumulative = 0
        for opt, w in zip(options, weights):
            cumulative += w
            if r <= cumulative:
                return opt

        return options[-1]

    async def record_daily_performance(self):
        today = datetime.utcnow().strftime("%Y-%m-%d")

        char_rows = await db.execute(
            "SELECT id FROM characters WHERE is_official = 1 AND is_public = 1",
            fetch_all=True,
        )

        for row in char_rows:
            char_id = row["id"]
            perf_id = f"perf_{uuid.uuid4().hex[:12]}"

            view_row = await db.execute(
                "SELECT COUNT(*) as cnt FROM character_views WHERE character_id = ? AND date(viewed_at) = ?",
                (char_id, today),
                fetch=True,
            )
            views = view_row["cnt"] if view_row else 0

            await db.execute(
                """INSERT OR REPLACE INTO character_performance
                   (id, character_id, date, views, chats_started)
                   VALUES (?, ?, ?, ?, ?)""",
                (perf_id, char_id, today, views, 0),
            )


performance_analyzer = PerformanceAnalyzer()
