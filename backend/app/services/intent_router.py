import logging
import re
from typing import Optional, Any
from enum import Enum

from ..core.config import get_settings

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    GREETING = "greeting"
    SIMPLE_QUESTION = "simple_question"
    EMOTIONAL = "emotional"
    STORY = "story"
    COMPLEX = "complex"
    ROLEPLAY = "roleplay"
    MEDIA_REQUEST = "media_request"
    UNKNOWN = "unknown"


GREETING_PATTERNS = [
    r"^(hi|hello|hey|你好|嗨|早上好|晚上好|下午好)[\s!.]*$",
    r"^(how are you|你好吗|最近怎么样)[\s?.]*$",
    r"^(what's up|最近怎样)[\s?.]*$",
]

SIMPLE_QUESTION_PATTERNS = [
    r"^(what is|who is|where is|when is|why is|how to)\s+\w+",
    r"^(什么是|谁是|在哪里|什么时候|为什么|怎么)\s+",
    r"^(yes|no|好的|不行|可以|是的|不是)[\s!.]*$",
    r"^(ok|okay|sure|没问题|好的)[\s!.]*$",
]

EMOTIONAL_PATTERNS = [
    r"(love|hate|sad|happy|angry|cry|miss|想念|喜欢|讨厌|开心|难过|生气|哭)",
    r"(feel|feeling|感觉|心情|情绪)",
    r"(lonely|alone|孤独|寂寞)",
    r"(worried|anxious|担心|焦虑)",
    r"(excited|期待|激动)",
]

STORY_PATTERNS = [
    r"(tell me a story|讲个故事|故事)",
    r"(continue|继续|下一步|then)",
    r"(what happens next|接下来)",
]

ROLEPLAY_PATTERNS = [
    r"(pretend|imagine|假设|假如|扮演)",
    r"(as if|仿佛)",
    r"(roleplay|角色扮演)",
]

MEDIA_REQUEST_PATTERNS = [
    r"(send|show|生成|发送|给我).*?(picture|image|photo|photo|图片|照片)",
    r"(generate|make|create).*?(video|视频)",
    r"(voice|audio|语音|声音)",
]


class IntentRouter:
    def __init__(self, confidence_threshold: float = 0.8):
        self.settings = get_settings()
        self._confidence_threshold = confidence_threshold
        self._pattern_weights = {
            IntentType.GREETING: 1.0,
            IntentType.SIMPLE_QUESTION: 0.9,
            IntentType.EMOTIONAL: 0.7,
            IntentType.STORY: 0.8,
            IntentType.ROLEPLAY: 0.8,
            IntentType.MEDIA_REQUEST: 0.95,
        }

    def classify(self, text: str) -> tuple[IntentType, float]:
        text_lower = text.lower().strip()

        for pattern in GREETING_PATTERNS:
            if re.match(pattern, text_lower, re.IGNORECASE):
                return IntentType.GREETING, 1.0

        for pattern in MEDIA_REQUEST_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return IntentType.MEDIA_REQUEST, 0.95

        for pattern in SIMPLE_QUESTION_PATTERNS:
            if re.match(pattern, text_lower, re.IGNORECASE):
                return IntentType.SIMPLE_QUESTION, 0.9

        for pattern in ROLEPLAY_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return IntentType.ROLEPLAY, 0.8

        for pattern in STORY_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return IntentType.STORY, 0.8

        emotional_matches = 0
        for pattern in EMOTIONAL_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                emotional_matches += 1

        if emotional_matches >= 2:
            return IntentType.EMOTIONAL, 0.85
        elif emotional_matches == 1:
            return IntentType.EMOTIONAL, 0.6

        if len(text) < 20:
            return IntentType.SIMPLE_QUESTION, 0.5

        return IntentType.COMPLEX, 0.3

    def should_use_local_model(self, text: str) -> tuple[bool, IntentType, float]:
        intent_type, confidence = self.classify(text)

        local_intents = [
            IntentType.GREETING,
            IntentType.SIMPLE_QUESTION,
        ]

        use_local = intent_type in local_intents and confidence >= self._confidence_threshold

        return use_local, intent_type, confidence

    def get_route_info(self, text: str) -> dict:
        use_local, intent_type, confidence = self.should_use_local_model(text)

        return {
            "intent": intent_type.value,
            "confidence": confidence,
            "use_local_model": use_local,
            "recommended_model": "local" if use_local else "cloud",
            "reason": self._get_reason(intent_type, confidence, use_local),
        }

    def _get_reason(self, intent: IntentType, confidence: float, use_local: bool) -> str:
        if use_local:
            return f"High-confidence {intent.value} ({confidence:.2f}), suitable for edge processing"
        else:
            return f"Complex intent {intent.value} ({confidence:.2f}), requires cloud inference"

    async def health_check(self) -> dict:
        return {
            "status": "healthy",
            "confidence_threshold": self._confidence_threshold,
            "supported_intents": [i.value for i in IntentType],
        }


intent_router = IntentRouter()