import pytest
from app.services.choice_matcher import ChoiceMatcher, MatchResult


class TestChoiceMatcher:
    @pytest.fixture
    def matcher(self):
        return ChoiceMatcher()

    @pytest.fixture
    def sample_choices(self):
        return [
            {
                "id": "choice_1",
                "text": "Tell her I love her",
                "next_node_id": "node_2",
                "effects": {"intimacy": 10}
            },
            {
                "id": "choice_2",
                "text": "Keep silent and look away",
                "next_node_id": "node_3",
                "effects": {"trust": -5}
            },
            {
                "id": "choice_3",
                "text": "Ask her about her day",
                "next_node_id": "node_4",
                "effects": {"trust": 5}
            }
        ]

    def test_keyword_match_basic(self, matcher, sample_choices):
        result = matcher._keyword_match(
            "I want to tell her that I love her",
            sample_choices
        )
        
        assert result.matched is True
        assert result.choice["id"] == "choice_1"
        assert result.confidence > 0

    def test_keyword_match_partial(self, matcher, sample_choices):
        result = matcher._keyword_match(
            "I'll stay quiet",
            sample_choices
        )
        
        assert result.matched is False or result.confidence < 0.5

    def test_keyword_match_no_match(self, matcher, sample_choices):
        result = matcher._keyword_match(
            "The weather is nice today",
            sample_choices
        )
        
        assert result.matched is False

    def test_semantic_match_high_similarity(self, matcher, sample_choices):
        result = matcher._semantic_match(
            "Tell her I love her so much",
            sample_choices,
            threshold=0.5
        )
        
        assert result.matched is True
        assert result.method == "semantic"

    def test_semantic_match_low_similarity(self, matcher, sample_choices):
        result = matcher._semantic_match(
            "What's for dinner?",
            sample_choices,
            threshold=0.7
        )
        
        assert result.matched is False

    def test_jaccard_similarity(self, matcher):
        sim = matcher._jaccard_similarity(
            "I love her so much",
            "I love her"
        )
        
        assert sim > 0.5

    def test_jaccard_similarity_no_overlap(self, matcher):
        sim = matcher._jaccard_similarity(
            "hello world",
            "goodbye moon"
        )
        
        assert sim == 0.0

    def test_extract_keywords(self, matcher, sample_choices):
        keywords = matcher._extract_keywords(sample_choices[0])
        
        assert "tell" in keywords or "love" in keywords
        assert "the" not in keywords
        assert "and" not in keywords

    def test_extract_keywords_cache(self, matcher, sample_choices):
        choice = sample_choices[0]
        
        keywords1 = matcher._extract_keywords(choice)
        keywords2 = matcher._extract_keywords(choice)
        
        assert keywords1 == keywords2
        assert choice["text"] in matcher._keyword_cache

    def test_calculate_direct_match(self, matcher):
        score = matcher._calculate_direct_match(
            "I want to tell her I love her",
            "Tell her I love her"
        )
        
        assert score > 0.5

    def test_calculate_direct_match_no_overlap(self, matcher):
        score = matcher._calculate_direct_match(
            "hello world",
            "goodbye moon"
        )
        
        assert score == 0.0

    def test_clear_cache(self, matcher, sample_choices):
        matcher._extract_keywords(sample_choices[0])
        assert len(matcher._keyword_cache) > 0
        
        matcher.clear_cache()
        assert len(matcher._keyword_cache) == 0

    @pytest.mark.asyncio
    async def test_match_keyword_success(self, matcher, sample_choices):
        result = await matcher.match(
            "I love her",
            sample_choices,
            use_llm_fallback=False
        )
        
        assert result.matched is True
        assert result.method == "keyword"

    @pytest.mark.asyncio
    async def test_match_no_choices(self, matcher):
        result = await matcher.match(
            "any message",
            [],
            use_llm_fallback=False
        )
        
        assert result.matched is False
        assert result.method == "no_choices"

    @pytest.mark.asyncio
    async def test_match_empty_message(self, matcher, sample_choices):
        result = await matcher.match(
            "",
            sample_choices,
            use_llm_fallback=False
        )
        
        assert result.matched is False


class TestMatchResult:
    def test_default_values(self):
        result = MatchResult(matched=False)
        
        assert result.matched is False
        assert result.choice is None
        assert result.confidence == 0.0
        assert result.method == ""

    def test_with_values(self):
        choice = {"id": "test", "text": "Test choice"}
        result = MatchResult(
            matched=True,
            choice=choice,
            confidence=0.85,
            method="keyword"
        )
        
        assert result.matched is True
        assert result.choice == choice
        assert result.confidence == 0.85
        assert result.method == "keyword"
