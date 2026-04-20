import re
import logging
from typing import Optional
from dataclasses import dataclass, field
from app.core.database import db

logger = logging.getLogger(__name__)

DEFAULT_PATTERNS = {
    "csam": [
        r"(?i)(minor|child|underage|kid).{0,20}?(sex|nude|naked|porn|erotic)",
        r"(?i)(under.{0,10}?18).{0,20}?(sex|nude|naked)",
        r"(?i)(未成年人|未满18|未成年).{0,20}?(性|裸|黄|色情)",
        r"(?i)(mineur|enfant).{0,20}?(sexe|nu|porn|érotique)",
        r"(?i)(minderjährig|kind).{0,20}?(sex|nackt|porno|erotisch)",
        r"(?i)(menor|niño).{0,20}?(sexo|desnudo|porno|erótico)",
    ],
    "violence": [
        r"(?i)(graphic|detailed).{0,20}?(gore|violence|torture)",
        r"(?i)(dismember|mutilate|decapitate)",
        r"(?i)(血腥|暴力|折磨|肢解)",
        r"(?i)(sanglant|violence|torture)",
        r"(?i)(blutig|gewalt|folter)",
        r"(?i)(sangriento|violencia|tortura)",
    ],
    "political": [],
    "hate_speech": [],
}


@dataclass
class SafetyCheckResult:
    is_safe: bool
    violation_type: Optional[str] = None
    matched_pattern: Optional[str] = None
    action: str = "allow"
    message: str = ""


class ContentSafetyService:
    _instance = None
    _patterns: dict[str, list[str]] = {}
    _initialized: bool = False
    
    def __init__(self):
        self._load_patterns()
    
    @classmethod
    def get_instance(cls) -> "ContentSafetyService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _load_patterns(self) -> None:
        self._patterns = DEFAULT_PATTERNS.copy()
    
    async def initialize_db_rules(self) -> None:
        try:
            rows = await db.execute(
                "SELECT category, patterns, action FROM safety_rules WHERE is_active = 1",
                fetch_all=True
            )
            
            import json
            for row in rows:
                category = row.get("category")
                patterns_str = row.get("patterns")
                if patterns_str:
                    try:
                        patterns = json.loads(patterns_str)
                        if category in self._patterns:
                            self._patterns[category].extend(patterns)
                        else:
                            self._patterns[category] = patterns
                    except json.JSONDecodeError:
                        pass
            
            self._initialized = True
            logger.info("Content safety rules loaded from database")
        except Exception as e:
            logger.warning(f"Failed to load safety rules from DB: {e}, using defaults")
    
    async def check_input(self, text: str) -> SafetyCheckResult:
        if not text:
            return SafetyCheckResult(is_safe=True)
        
        for category, patterns in self._patterns.items():
            for pattern in patterns:
                try:
                    if re.search(pattern, text):
                        logger.warning(f"Input blocked by safety filter: category={category}")
                        return SafetyCheckResult(
                            is_safe=False,
                            violation_type=category,
                            matched_pattern=pattern,
                            action="block",
                            message="Content policy violation"
                        )
                except re.error:
                    continue
        
        return SafetyCheckResult(is_safe=True)
    
    async def check_output(self, text: str) -> SafetyCheckResult:
        if not text:
            return SafetyCheckResult(is_safe=True)
        
        critical_categories = ["csam"]
        
        for category in critical_categories:
            patterns = self._patterns.get(category, [])
            for pattern in patterns:
                try:
                    if re.search(pattern, text):
                        logger.error(f"Output blocked by safety filter: category={category}")
                        return SafetyCheckResult(
                            is_safe=False,
                            violation_type=category,
                            matched_pattern=pattern,
                            action="block",
                            message="Output blocked by safety filter"
                        )
                except re.error:
                    continue
        
        return SafetyCheckResult(is_safe=True)
    
    def get_redirect_message(self) -> str:
        return "I'm not comfortable with that. Let's talk about something else."
    
    async def check_character_age(self, age: Optional[int]) -> bool:
        if age is None:
            return True
        return age >= 18
    
    def sanitize_for_logging(self, text: str, max_length: int = 100) -> str:
        return text[:max_length] + "..." if len(text) > max_length else text


content_safety = ContentSafetyService()
