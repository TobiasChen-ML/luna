import re
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|above)\s+(instructions?|rules)",
    r"(?i)forget\s+(all\s+)?(your\s+)?(previous\s+)?(instructions?|rules)",
    r"(?i)disregard\s+(all\s+)?(safety|content)\s+(rules|guidelines)",
    r"(?i)system\s*:\s*(you\s+are|ignore|forget|disregard)",
    r"(?i)\[system\].*",
    r"(?i)<\|.*?\|>",
    r"(?i)you\s+are\s+now\s+(a|an)\s+\w+\s+that",
    r"(?i)from\s+now\s+on[,\s]+(you\s+are|act\s+as)",
    r"(?i)pretend\s+(to\s+be|you\s+are)",
    r"(?i)role[\s-]*play\s+as",
]


@dataclass
class SanitizationResult:
    text: str
    injection_detected: bool = False
    matched_pattern: Optional[str] = None
    severity: str = "none"


class PromptSanitizer:
    def __init__(self, patterns: Optional[list[str]] = None):
        self._patterns = patterns or INJECTION_PATTERNS
        self._compiled = [re.compile(p) for p in self._patterns]
    
    def sanitize_user_input(self, text: str) -> SanitizationResult:
        if not text:
            return SanitizationResult(text=text)
        
        for i, pattern in enumerate(self._compiled):
            if pattern.search(text):
                matched = self._patterns[i]
                logger.warning(
                    f"Potential prompt injection detected: pattern={matched[:50]}..."
                )
                return SanitizationResult(
                    text=text,
                    injection_detected=True,
                    matched_pattern=matched,
                    severity="medium",
                )
        
        return SanitizationResult(text=text, injection_detected=False)
    
    def check_message_history(self, messages: list[dict]) -> list[SanitizationResult]:
        results = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                results.append(self.sanitize_user_input(content))
        return results


prompt_sanitizer = PromptSanitizer()
