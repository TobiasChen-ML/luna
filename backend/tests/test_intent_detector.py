"""
Tests for intent_detector module
Supports: English, French, German, Spanish
"""

import pytest
from app.services.intent_detector import (
    detect_video_intent_keywords,
    is_likely_video_request,
    needs_llm_verification,
)


class TestDetectVideoIntentKeywords:
    """Tests for detect_video_intent_keywords function."""

    def test_empty_message(self):
        """Empty message should not be detected as video request."""
        is_video, confidence = detect_video_intent_keywords("")
        assert is_video is False
        assert confidence == 0.0

    def test_none_message(self):
        """None message should not be detected as video request."""
        is_video, confidence = detect_video_intent_keywords(None)
        assert is_video is False
        assert confidence == 0.0

    def test_high_confidence_english_keywords(self):
        """English high confidence keywords should be detected."""
        test_cases = [
            "make a video for me",
            "record a video",
            "send me a video",
            "take a video",
            "shoot a video",
            "selfie video",
        ]
        for msg in test_cases:
            is_video, confidence = detect_video_intent_keywords(msg)
            assert is_video is True, f"Failed for: {msg}"
            assert confidence >= 0.9, f"Low confidence for: {msg}"

    def test_high_confidence_french_keywords(self):
        """French high confidence keywords should be detected."""
        test_cases = [
            "fais une vidéo",
            "faire une vidéo",
            "créer une vidéo",
            "envoie une vidéo",
            "une vidéo s'il te plaît",
        ]
        for msg in test_cases:
            is_video, confidence = detect_video_intent_keywords(msg)
            assert is_video is True, f"Failed for: {msg}"
            assert confidence >= 0.9, f"Low confidence for: {msg}"

    def test_high_confidence_german_keywords(self):
        """German high confidence keywords should be detected."""
        test_cases = [
            "mach ein video",
            "mache ein video",
            "ein video aufnehmen",
            "video bitte",
            "ein video von dir",
        ]
        for msg in test_cases:
            is_video, confidence = detect_video_intent_keywords(msg)
            assert is_video is True, f"Failed for: {msg}"
            assert confidence >= 0.9, f"Low confidence for: {msg}"

    def test_high_confidence_spanish_keywords(self):
        """Spanish high confidence keywords should be detected."""
        test_cases = [
            "haz un video",
            "hacer un video",
            "crear un video",
            "envía un video",
            "graba un video",
        ]
        for msg in test_cases:
            is_video, confidence = detect_video_intent_keywords(msg)
            assert is_video is True, f"Failed for: {msg}"
            assert confidence >= 0.9, f"Low confidence for: {msg}"

    def test_negative_context_watching_video(self):
        """Messages about watching videos should NOT be detected as requests."""
        test_cases = [
            "I saw a video about cats",
            "I watched a video yesterday",
            "the video was so funny",
            "that video is great",
            "in the video he said",
            "la vidéo était drôle",
            "el vídeo fue gracioso",
            "das video war lustig",
        ]
        for msg in test_cases:
            is_video, confidence = detect_video_intent_keywords(msg)
            assert is_video is False, f"Should not detect as video request: {msg}"

    def test_medium_confidence_with_request_indicator(self):
        """Single video keyword with request indicator should have medium confidence."""
        test_cases = [
            "please send video",
            "can you video",
            "s'il te plaît vidéo",
            "bitte video",
            "por favor video",
        ]
        for msg in test_cases:
            is_video, confidence = detect_video_intent_keywords(msg)
            assert is_video is True, f"Failed for: {msg}"
            assert confidence >= 0.5, f"Low confidence for: {msg}"

    def test_normal_chat_messages(self):
        """Normal chat messages should not be detected as video requests."""
        test_cases = [
            "How are you doing?",
            "What's for dinner?",
            "Comment ça va?",
            "Wie geht es dir?",
            "¿Cómo estás?",
            "I like watching movies",
        ]
        for msg in test_cases:
            is_video, confidence = detect_video_intent_keywords(msg)
            assert is_video is False, f"Should not detect as video request: {msg}"

    def test_animate_keyword(self):
        """Animate keyword should be detected."""
        is_video, confidence = detect_video_intent_keywords("animate this for me")
        assert is_video is True
        assert confidence >= 0.5


class TestIsLikelyVideoRequest:
    """Tests for is_likely_video_request function."""

    def test_high_confidence_request(self):
        """High confidence requests should return True."""
        assert is_likely_video_request("make a video for me") is True
        assert is_likely_video_request("fais une vidéo") is True
        assert is_likely_video_request("mach ein video") is True
        assert is_likely_video_request("haz un video") is True

    def test_low_confidence_request(self):
        """Low confidence or non-requests should return False."""
        assert is_likely_video_request("I saw a video") is False
        assert is_likely_video_request("hello") is False
        assert is_likely_video_request("bonjour") is False

    def test_custom_threshold(self):
        """Custom threshold should work correctly."""
        assert is_likely_video_request("video", threshold=0.4) is True
        assert is_likely_video_request("video", threshold=0.9) is False


class TestNeedsLLMVerification:
    """Tests for needs_llm_verification function."""

    def test_high_confidence_no_verification_needed(self):
        """High confidence requests don't need LLM verification."""
        assert needs_llm_verification("make a video for me") is False
        assert needs_llm_verification("fais une vidéo") is False

    def test_no_video_intent_no_verification_needed(self):
        """Non-video requests don't need LLM verification."""
        assert needs_llm_verification("hello") is False
        assert needs_llm_verification("bonjour") is False

    def test_medium_confidence_needs_verification(self):
        """Medium confidence requests need LLM verification."""
        assert needs_llm_verification("video") is True
        assert needs_llm_verification("vidéo") is True
        assert needs_llm_verification("vídeo") is True
