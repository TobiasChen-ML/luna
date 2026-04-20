"""
Video Intent Handler

Handles video request detection and generates appropriate decline messages
based on character personality.
"""

import logging
from typing import Optional, Any

from .intent_detector import (
    detect_video_intent_keywords,
    is_likely_video_request,
    needs_llm_verification,
)

logger = logging.getLogger(__name__)


class VideoIntentHandler:
    """Handles detection and response for video intent requests."""
    
    def __init__(self):
        self._decline_prompt_template = """The user asked for a video, but you cannot create or send videos. 
You CAN create photos/images. Politely decline the video request in a way that fits your personality, 
and offer to take a photo instead. Keep your response short and natural (1-2 sentences).

Your personality: {personality}

User's request: {user_message}

Respond naturally as if chatting, declining the video request and suggesting a photo instead:"""
    
    async def handle_video_intent(
        self,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
    ) -> Optional[str]:
        """
        Check if the message is a video request and generate decline message if so.
        
        Args:
            user_message: The user's message text
            character: Character data including personality info
            llm_service: LLM service for generating responses and intent detection
        
        Returns:
            Optional[str]: None if not a video request (continue normal chat),
                          or a decline message string if it is a video request
        """
        if not user_message or not user_message.strip():
            return None
        
        is_video, confidence = detect_video_intent_keywords(user_message)
        
        if not is_video:
            logger.debug(f"Keyword detection: not a video request")
            return None
        
        logger.info(f"Video intent detected with confidence {confidence}")
        
        if confidence >= 0.8:
            logger.info("High confidence video intent - generating decline message")
            return await self._generate_decline_message(
                user_message, character, llm_service
            )
        
        if needs_llm_verification(user_message):
            logger.info("Medium confidence - verifying with LLM")
            try:
                llm_result = await self._verify_with_llm(
                    user_message, llm_service
                )
                if llm_result.get("is_video_request", False):
                    logger.info("LLM confirmed video request - generating decline")
                    return await self._generate_decline_message(
                        user_message, character, llm_service
                    )
                else:
                    logger.info("LLM determined not a video request - continuing normal chat")
                    return None
            except Exception as e:
                logger.warning(f"LLM verification failed: {e} - falling back to decline")
                return await self._generate_decline_message(
                    user_message, character, llm_service
                )
        
        return None
    
    async def _verify_with_llm(
        self,
        user_message: str,
        llm_service: Any,
    ) -> dict[str, Any]:
        """
        Use LLM to verify if the message is actually a video request.
        
        Returns dict with keys:
        - is_video_request: bool
        - confidence: float
        - reasoning: str (optional)
        """
        try:
            result = await llm_service.detect_video_intent(user_message)
            return result
        except Exception as e:
            logger.error(f"LLM video intent detection failed: {e}")
            return {"is_video_request": False, "confidence": 0.0}
    
    async def _generate_decline_message(
        self,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
    ) -> str:
        """
        Generate a decline message based on character personality.
        
        The message should:
        1. Politely decline the video request
        2. Offer to take a photo instead
        3. Match the character's personality/tone
        """
        personality = self._extract_personality(character)
        character_name = character.get("name", "我")
        
        prompt = self._decline_prompt_template.format(
            personality=personality,
            user_message=user_message,
        )
        
        try:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_message},
            ]
            
            response = await llm_service.generate(
                messages=messages,
                temperature=0.8,
                max_tokens=150,
            )
            
            decline_message = response.content.strip()
            
            if decline_message and len(decline_message) > 10:
                return decline_message
            
        except Exception as e:
            logger.error(f"Failed to generate decline message: {e}")
        
        return self._get_fallback_decline_message(character_name, personality)
    
    def _extract_personality(self, character: dict[str, Any]) -> str:
        """Extract personality description from character data."""
        parts = []
        
        if character.get("personality_summary"):
            parts.append(character["personality_summary"])
        
        if character.get("personality_tags"):
            tags = character["personality_tags"]
            if isinstance(tags, list):
                parts.append(", ".join(tags[:5]))
            elif isinstance(tags, str):
                parts.append(tags)
        
        if character.get("backstory"):
            backstory = character["backstory"]
            if len(backstory) > 200:
                backstory = backstory[:200] + "..."
            parts.append(backstory)
        
        if parts:
            return " ".join(parts)
        
        return "friendly and warm"
    
    def _get_fallback_decline_message(
        self,
        character_name: str,
        personality: str,
    ) -> str:
        """Get a fallback decline message if LLM generation fails."""
        if "可爱" in personality or "cute" in personality.lower():
            return f"抱歉啦~人家现在没办法给你拍视频呢，不过可以给你拍张照片哦？📸"
        
        if "高冷" in personality or "cold" in personality.lower():
            return f"我没法录视频。不过...拍照倒是没问题。"
        
        if "温柔" in personality or "gentle" in personality.lower():
            return f"不好意思，我现在还不会录视频呢。不过我可以给你拍张照片，好吗？"
        
        if "活泼" in personality or "energetic" in personality.lower():
            return f"哎呀，拍视频还不行呢！但我可以给你拍张超美的照片~要不要？"
        
        return f"抱歉，我现在没法拍视频。不过我可以给你拍张照片，要不要试试？"


video_intent_handler = VideoIntentHandler()
