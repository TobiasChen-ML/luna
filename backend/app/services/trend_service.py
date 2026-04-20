import json
import logging
import uuid
from datetime import datetime
from typing import Optional

from app.core.database import db

logger = logging.getLogger(__name__)

TREND_KEYWORDS = [
    "AI girlfriend",
    "virtual girlfriend",
    "anime girl",
    "AI chatbot",
    "character AI",
    "virtual companion",
    "AI companion",
    "chat with AI",
    "roleplay AI",
    "AI character",
    "waifu",
    "anime girlfriend",
]


class TrendService:
    _instance = None

    def __init__(self):
        self._llm_service = None

    @classmethod
    def get_instance(cls) -> "TrendService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _get_llm_service(self):
        if self._llm_service is None:
            from app.services.llm_service import LLMService
            self._llm_service = LLMService.get_instance()
        return self._llm_service

    async def fetch_google_trends(self) -> list[dict]:
        try:
            from pytrends.request import TrendReq

            pytrends = TrendReq(hl="en-US", tz=360)
            pytrends.build_payload(TREND_KEYWORDS, cat=0, timeframe="now 7-d")

            related_queries = pytrends.related_queries()
            trends = []

            for kw, data in related_queries.items():
                if data.get("rising") is not None:
                    for _, row in data["rising"].iterrows():
                        trends.append({
                            "keyword": row.get("query", ""),
                            "volume": row.get("value", "unknown"),
                            "source": "google_trends",
                        })

            seen = set()
            unique_trends = []
            for t in trends:
                if t["keyword"] and t["keyword"] not in seen:
                    seen.add(t["keyword"])
                    unique_trends.append(t)

            return unique_trends[:50]

        except ImportError:
            logger.warning("pytrends not installed, returning mock trends")
            return self._get_mock_trends()
        except Exception as e:
            logger.error(f"Failed to fetch Google Trends: {e}")
            return self._get_mock_trends()

    def _get_mock_trends(self) -> list[dict]:
        return [
            {"keyword": "anime girlfriend", "volume": "high", "source": "mock"},
            {"keyword": "AI companion chat", "volume": "high", "source": "mock"},
            {"keyword": "roleplay character", "volume": "medium", "source": "mock"},
            {"keyword": "waifu chat", "volume": "medium", "source": "mock"},
            {"keyword": "virtual relationship", "volume": "medium", "source": "mock"},
        ]

    async def map_keywords_to_attributes(self, keywords: list[str]) -> dict:
        llm = self._get_llm_service()

        prompt = f"""Map these trending search keywords to character attributes for an AI companion app.

Keywords: {keywords}

Return a JSON object with these fields:
- suggested_occupations: list of 5-10 occupation types that match these keywords
- suggested_personality_tags: list of 5-10 personality traits that users might be looking for
- suggested_styles: list of 3-5 visual styles (e.g., "anime", "realistic", "fantasy")
- suggested_ethnicities: list of 3-5 ethnicities that match the trends
- suggested_scenarios: list of 3-5 roleplay scenarios or settings

Respond with valid JSON only. No markdown."""

        try:
            response = await llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )

            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content
                content = content.rsplit("```", 1)[0] if "```" in content else content

            return json.loads(content)

        except Exception as e:
            logger.error(f"Failed to map keywords to attributes: {e}")
            return {
                "suggested_occupations": ["college_student", "office_worker", "model", "gamer", "idol"],
                "suggested_personality_tags": ["gentle", "playful", "caring", "flirty", "mysterious"],
                "suggested_styles": ["anime", "realistic"],
                "suggested_ethnicities": ["asian", "white", "latina"],
                "suggested_scenarios": ["romance", "friendship", "fantasy"],
            }

    async def save_trends(self, trends: list[dict]) -> int:
        saved = 0
        now = datetime.utcnow().isoformat()

        for t in trends:
            trend_id = f"trend_{uuid.uuid4().hex[:12]}"

            await db.execute(
                """INSERT OR REPLACE INTO trend_keywords
                   (id, keyword, source, search_volume, detected_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (trend_id, t["keyword"], t.get("source", "google_trends"), 
                 str(t.get("volume", "unknown")), now, now),
            )
            saved += 1

        return saved

    async def get_trend_weighted_attributes(self) -> dict:
        rows = await db.execute(
            "SELECT keyword, relevance_score FROM trend_keywords ORDER BY relevance_score DESC LIMIT 50",
            fetch_all=True,
        )

        keywords = [row["keyword"] for row in rows] if rows else TREND_KEYWORDS

        return await self.map_keywords_to_attributes(keywords)

    async def refresh_trends(self) -> dict:
        trends = await self.fetch_google_trends()

        if not trends:
            return {"success": False, "message": "No trends fetched"}

        attributes = await self.map_keywords_to_attributes([t["keyword"] for t in trends])

        saved = await self.save_trends(trends)

        return {
            "success": True,
            "trends_fetched": len(trends),
            "trends_saved": saved,
            "attributes": attributes,
        }

    async def get_stored_trends(self, limit: int = 50) -> list[dict]:
        rows = await db.execute(
            """SELECT id, keyword, source, search_volume, trend_direction, 
                      relevance_score, detected_at
               FROM trend_keywords
               ORDER BY relevance_score DESC, detected_at DESC
               LIMIT ?""",
            (limit,),
            fetch_all=True,
        )

        return [dict(row) for row in rows] if rows else []


trend_service = TrendService()
