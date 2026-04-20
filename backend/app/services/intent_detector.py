"""
Intent Detection Service

Provides fast keyword-based intent detection for video requests.
Used as first-pass detection before falling back to LLM-based detection.
Supports: English, French, German, Spanish
"""

import re
from typing import Tuple


VIDEO_KEYWORDS_HIGH_CONFIDENCE_EN = [
    "make a video", "record a video", "create a video",
    "send a video", "take a video", "shoot a video",
    "video please", "video of you", "a video for me",
    "make me a video", "send me a video", "selfie video",
]

VIDEO_KEYWORDS_HIGH_CONFIDENCE_FR = [
    "fais une vidéo", "faire une vidéo", "créer une vidéo",
    "envoie une vidéo", "une vidéo s'il te plaît",
    "vidéo de toi", "une vidéo pour moi",
    "enregistre une vidéo", "tourne une vidéo",
]

VIDEO_KEYWORDS_HIGH_CONFIDENCE_DE = [
    "mach ein video", "mache ein video", "ein video aufnehmen",
    "video bitte", "ein video von dir", "video für mich",
    "erstell ein video", "sende ein video",
]

VIDEO_KEYWORDS_HIGH_CONFIDENCE_ES = [
    "haz un video", "hacer un video", "crear un video",
    "envía un video", "graba un video", "un video por favor",
    "un video de ti", "un video para mí",
]

VIDEO_KEYWORDS_MEDIUM_CONFIDENCE = [
    "video", "animate", "animation",
    "vidéo", "vídeo",
]

NEGATIVE_CONTEXT_PATTERNS = [
    r"saw a video",
    r"watched a video",
    r"the video",
    r"that video",
    r"in the video",
    r"video was",
    r"video is",
    r"la vidéo",  
    r"el vídeo",
    r"das video",
]

REQUEST_INDICATORS_EN = [
    "please", "can you", "could you", "i want", "i'd like",
    "make me", "send me", "show me",
]

REQUEST_INDICATORS_FR = [
    "s'il te plaît", "s'il vous plaît", "peux-tu", "peux tu",
    "je veux", "j'aimerais", "fais-moi", "montre-moi",
]

REQUEST_INDICATORS_DE = [
    "bitte", "kannst du", "ich will", "ich möchte",
    "mach mir", "zeig mir",
]

REQUEST_INDICATORS_ES = [
    "por favor", "puedes", "quiero", "me gustaría",
    "hazme", "muéstrame",
]


def detect_video_intent_keywords(message: str) -> Tuple[bool, float]:
    """
    Detect if the message is a video request using keyword matching.
    Supports: English, French, German, Spanish
    
    Returns:
        Tuple[bool, float]: (is_video_intent, confidence)
        - is_video_intent: True if the message appears to be a video request
        - confidence: 0.0 to 1.0, indicating how confident the detection is
    """
    if not message or not message.strip():
        return (False, 0.0)
    
    msg_lower = message.lower().strip()
    
    for pattern in NEGATIVE_CONTEXT_PATTERNS:
        if re.search(pattern, msg_lower):
            return (False, 0.0)
    
    for kw in VIDEO_KEYWORDS_HIGH_CONFIDENCE_EN:
        if kw in msg_lower:
            return (True, 0.95)
    
    for kw in VIDEO_KEYWORDS_HIGH_CONFIDENCE_FR:
        if kw in msg_lower:
            return (True, 0.95)
    
    for kw in VIDEO_KEYWORDS_HIGH_CONFIDENCE_DE:
        if kw in msg_lower:
            return (True, 0.95)
    
    for kw in VIDEO_KEYWORDS_HIGH_CONFIDENCE_ES:
        if kw in msg_lower:
            return (True, 0.95)
    
    for kw in VIDEO_KEYWORDS_MEDIUM_CONFIDENCE:
        if kw in msg_lower:
            all_indicators = (
                REQUEST_INDICATORS_EN + 
                REQUEST_INDICATORS_FR + 
                REQUEST_INDICATORS_DE + 
                REQUEST_INDICATORS_ES
            )
            has_request_indicator = any(
                ind in msg_lower for ind in all_indicators
            )
            if has_request_indicator:
                return (True, 0.75)
            else:
                return (True, 0.5)
    
    return (False, 0.0)


def is_likely_video_request(message: str, threshold: float = 0.7) -> bool:
    """
    Quick check if message is likely a video request.
    
    Args:
        message: The user message to check
        threshold: Confidence threshold (default 0.7)
    
    Returns:
        bool: True if confidence >= threshold
    """
    is_video, confidence = detect_video_intent_keywords(message)
    return is_video and confidence >= threshold


def needs_llm_verification(message: str) -> bool:
    """
    Check if the message needs LLM-based verification.
    
    Returns True when:
    - Keyword detection found a potential video request
    - But confidence is low (0.5-0.7), indicating uncertainty
    
    Args:
        message: The user message to check
    
    Returns:
        bool: True if LLM verification is recommended
    """
    is_video, confidence = detect_video_intent_keywords(message)
    return is_video and 0.5 <= confidence < 0.8
