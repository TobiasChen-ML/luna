import logging
import re
from typing import Optional, Any
from dataclasses import dataclass

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


@dataclass
class MatchResult:
    matched: bool
    choice: Optional[dict[str, Any]] = None
    confidence: float = 0.0
    method: str = ""


class ChoiceMatcher:
    _instance = None

    def __init__(self):
        self._keyword_cache: dict[str, list[str]] = {}

    @classmethod
    def get_instance(cls) -> "ChoiceMatcher":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def match(
        self,
        user_message: str,
        choices: list[dict[str, Any]],
        threshold: float = 0.7,
        use_llm_fallback: bool = True
    ) -> MatchResult:
        if not choices:
            return MatchResult(matched=False, method="no_choices")

        result = self._keyword_match(user_message, choices)
        if result.matched:
            logger.debug(f"Keyword match success: confidence={result.confidence:.2f}")
            return result

        result = self._semantic_match(user_message, choices, threshold)
        if result.matched:
            logger.debug(f"Semantic match success: confidence={result.confidence:.2f}")
            return result

        if use_llm_fallback:
            result = await self._llm_classify(user_message, choices)
            if result.matched:
                logger.debug(f"LLM match success: confidence={result.confidence:.2f}")
                return result

        return MatchResult(matched=False, method="no_match")

    def _keyword_match(self, user_message: str, choices: list[dict]) -> MatchResult:
        user_lower = user_message.lower()
        best_match = None
        best_score = 0.0

        for choice in choices:
            keywords = self._extract_keywords(choice)
            choice_text = choice.get("text", "").lower()

            score = 0.0
            matched_keywords = 0

            for keyword in keywords:
                if keyword in user_lower:
                    matched_keywords += 1

            if matched_keywords > 0:
                score = matched_keywords / len(keywords) if keywords else 0

            direct_match_score = self._calculate_direct_match(user_lower, choice_text)
            score = max(score, direct_match_score)

            if score > best_score:
                best_score = score
                best_match = choice

        if best_match and best_score >= 0.5:
            return MatchResult(
                matched=True,
                choice=best_match,
                confidence=min(best_score, 1.0),
                method="keyword"
            )

        return MatchResult(matched=False, method="keyword")

    def _semantic_match(
        self,
        user_message: str,
        choices: list[dict],
        threshold: float
    ) -> MatchResult:
        user_lower = user_message.lower()
        best_match = None
        best_similarity = 0.0

        for choice in choices:
            choice_text = choice.get("text", "").lower()
            similarity = self._jaccard_similarity(user_lower, choice_text)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = choice

        if best_match and best_similarity >= threshold:
            return MatchResult(
                matched=True,
                choice=best_match,
                confidence=best_similarity,
                method="semantic"
            )

        return MatchResult(matched=False, method="semantic")

    async def _llm_classify(
        self,
        user_message: str,
        choices: list[dict]
    ) -> MatchResult:
        try:
            llm = LLMService.get_instance()

            choice_texts = [c.get("text", "") for c in choices]

            schema = {
                "type": "object",
                "properties": {
                    "matched_index": {
                        "type": "integer",
                        "minimum": -1,
                        "maximum": len(choices) - 1
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1
                    },
                    "reasoning": {"type": "string"}
                },
                "required": ["matched_index", "confidence"]
            }

            system_prompt = f"""You are a choice matcher for an interactive story.

Given a user's message, determine which predefined choice it best matches.

Available choices:
{chr(10).join(f"{i}. {text}" for i, text in enumerate(choice_texts))}

Rules:
- Return the index (0-{len(choices)-1}) of the best matching choice
- Return -1 if no choice matches well
- Only match if the user clearly intends to make that choice
- Consider synonyms, paraphrases, and natural language variations

Respond with valid JSON only."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]

            response = await llm.generate_structured(
                messages,
                schema,
                temperature=0.1,
                provider="deepseek"
            )

            data = response.data
            matched_index = data.get("matched_index", -1)
            confidence = data.get("confidence", 0.0)

            if matched_index >= 0 and matched_index < len(choices):
                return MatchResult(
                    matched=True,
                    choice=choices[matched_index],
                    confidence=confidence,
                    method="llm"
                )

            return MatchResult(matched=False, method="llm")

        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return MatchResult(matched=False, method="llm_error")

    def _extract_keywords(self, choice: dict) -> list[str]:
        text = choice.get("text", "")
        if text in self._keyword_cache:
            return self._keyword_cache[text]

        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "under", "again", "further",
            "then", "once", "here", "there", "when", "where", "why",
            "how", "all", "each", "few", "more", "most", "other", "some",
            "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "just", "and", "but", "if", "or",
            "because", "until", "while", "this", "that", "these", "those",
            "i", "me", "my", "we", "our", "you", "your", "he", "him",
            "his", "she", "her", "it", "its", "they", "them", "their",
            "what", "which", "who", "whom"
        }

        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        self._keyword_cache[text] = keywords
        return keywords

    def _calculate_direct_match(self, user_text: str, choice_text: str) -> float:
        user_words = set(re.findall(r'\b\w+\b', user_text))
        choice_words = set(re.findall(r'\b\w+\b', choice_text))

        if not choice_words:
            return 0.0

        overlap = user_words & choice_words
        return len(overlap) / len(choice_words)

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        words1 = set(re.findall(r'\b\w+\b', text1))
        words2 = set(re.findall(r'\b\w+\b', text2))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def clear_cache(self):
        self._keyword_cache.clear()


choice_matcher = ChoiceMatcher()
