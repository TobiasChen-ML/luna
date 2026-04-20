"""
Image Intent Handler

Handles image request detection and triggers image generation.
"""

import logging
from typing import Optional, Any

from .intent_detector import detect_video_intent_keywords

logger = logging.getLogger(__name__)

IMAGE_KEYWORDS = [
    "photo", "picture", "image", "自拍", "照片", "图片", "拍照", 
    "send me a", "show me", "take a", "snap", "selfie",
    "发张", "发个", "给我看", "来张", "拍张", 
    "shoot", "camera", "镜头", "pose", "姿势",
    "穿着", "穿著", "wearing", "dress", "outfit",
    "undress", "脱", "naked", "nude", "裸",
    "sexy", "性感", "hot", "beautiful",
]


def detect_image_intent_keywords(message: str) -> tuple[bool, float]:
    """
    Quick keyword-based detection for image requests.
    
    Returns:
        tuple[bool, float]: (is_image_request, confidence)
    """
    message_lower = message.lower()
    
    matches = sum(1 for kw in IMAGE_KEYWORDS if kw in message_lower)
    
    if matches == 0:
        return False, 0.0
    
    high_confidence_keywords = [
        "自拍", "照片", "拍照", "selfie", "take a photo",
        "send me a photo", "发张照片", "来张照片", "shoot photo",
        "拍张照", "给我拍", "pose for", "摆个姿势",
    ]
    
    for kw in high_confidence_keywords:
        if kw in message_lower:
            return True, 0.85 + min(0.15, matches * 0.02)
    
    if matches >= 3:
        return True, 0.7 + min(0.2, (matches - 3) * 0.05)
    
    if matches >= 1:
        return True, 0.5 + matches * 0.1
    
    return False, 0.0


class ImageIntentHandler:
    """Handles detection and generation for image intent requests."""
    
    def __init__(self):
        self._accept_prompt_template = """The user asked for a photo/image. 
Generate a short, natural response (1-2 sentences) as if you're agreeing to take a photo, 
matching your personality.

Your personality: {personality}

User's request: {user_message}

Respond naturally as if you're about to take a photo:"""
    
    async def handle_image_intent(
        self,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
        media_service: Any,
        session_id: Optional[str] = None,
        character_image_url: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Check if the message is an image request and trigger generation if so.
        
        Args:
            user_message: The user's message text
            character: Character data
            llm_service: LLM service for intent detection and response generation
            media_service: Media service for image generation
            session_id: Current chat session ID
            character_image_url: Character's base image URL for img2img
        
        Returns:
            dict with keys:
            - is_image_request: bool
            - task_id: Optional[str] - Image generation task ID
            - response_message: Optional[str] - Message to send to user
            - prompt: Optional[str] - Extracted image prompt
        """
        result = {
            "is_image_request": False,
            "task_id": None,
            "response_message": None,
            "prompt": None,
        }
        
        if not user_message or not user_message.strip():
            return result
        
        is_video, _ = detect_video_intent_keywords(user_message)
        if is_video:
            logger.debug("Message is a video request, not image")
            return result
        
        is_image, confidence = detect_image_intent_keywords(user_message)
        
        if not is_image:
            return result
        
        logger.info(f"Image intent detected with confidence {confidence}")
        
        if confidence >= 0.7:
            return await self._trigger_image_generation(
                user_message=user_message,
                character=character,
                llm_service=llm_service,
                media_service=media_service,
                session_id=session_id,
                character_image_url=character_image_url,
            )
        
        if confidence >= 0.5:
            try:
                llm_result = await self._verify_with_llm(
                    user_message, character, llm_service
                )
                if llm_result.get("is_image_request", False):
                    return await self._trigger_image_generation(
                        user_message=user_message,
                        character=character,
                        llm_service=llm_service,
                        media_service=media_service,
                        session_id=session_id,
                        character_image_url=character_image_url,
                        extracted_prompt=llm_result.get("prompt"),
                    )
            except Exception as e:
                logger.warning(f"LLM verification failed: {e}")
        
        return result
    
    async def _verify_with_llm(
        self,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
    ) -> dict[str, Any]:
        """Use LLM to verify image intent and extract prompt."""
        try:
            result = await llm_service.detect_image_intent(
                user_message,
                context={"character_name": character.get("name")}
            )
            return result
        except Exception as e:
            logger.error(f"LLM image intent detection failed: {e}")
            return {"is_image_request": False, "confidence": 0.0}
    
    async def _trigger_image_generation(
        self,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
        media_service: Any,
        session_id: Optional[str],
        character_image_url: Optional[str],
        extracted_prompt: Optional[str] = None,
    ) -> dict[str, Any]:
        """Trigger image generation and return result."""
        from app.services.media import NovitaImageProvider
        
        provider = media_service.get_image_provider("novita")
        if not provider or not isinstance(provider, NovitaImageProvider):
            return {
                "is_image_request": True,
                "task_id": None,
                "response_message": "抱歉，图片生成服务暂时不可用。",
                "prompt": None,
            }
        
        prompt = extracted_prompt or await self._extract_image_prompt(
            user_message, character, llm_service
        )
        
        if not prompt:
            prompt = user_message
        
        character_name = character.get("name", "")
        prompt = f"{character_name}, {prompt}"
        
        try:
            if character_image_url:
                task_id = await provider.img2img_async(
                    init_image_url=character_image_url,
                    prompt=prompt,
                    strength=0.75,
                )
            else:
                task_id = await provider.txt2img_async(
                    prompt=prompt,
                    restore_faces=True,
                )
            
            response_message = await self._generate_accept_message(
                user_message, character, llm_service
            )
            
            return {
                "is_image_request": True,
                "task_id": task_id,
                "response_message": response_message,
                "prompt": prompt,
            }
        
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return {
                "is_image_request": True,
                "task_id": None,
                "response_message": "抱歉，生成图片时遇到了问题，请稍后再试。",
                "prompt": prompt,
            }
    
    async def _extract_image_prompt(
        self,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
    ) -> Optional[str]:
        """Extract a clean image generation prompt from user message."""
        extract_schema = {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Clean, detailed image generation prompt"
                },
                "style": {"type": "string"},
            },
            "required": ["prompt"]
        }
        
        system_prompt = f"""Extract a clean image generation prompt from the user's message.

Character: {character.get('name', 'a person')}
Gender: {character.get('gender', 'female')}

Rules:
1. Describe the visual scene the user wants
2. Include pose, clothing, setting, expression
3. Make it detailed enough for an AI to generate
4. Remove any conversational elements

Respond with valid JSON only."""
        
        try:
            response = await llm_service.generate_structured(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                schema=extract_schema,
                temperature=0.3,
            )
            return response.data.get("prompt")
        except Exception as e:
            logger.error(f"Prompt extraction failed: {e}")
            return None
    
    async def _generate_accept_message(
        self,
        user_message: str,
        character: dict[str, Any],
        llm_service: Any,
    ) -> str:
        """Generate a message accepting the photo request."""
        personality = self._extract_personality(character)
        
        prompt = self._accept_prompt_template.format(
            personality=personality,
            user_message=user_message,
        )
        
        try:
            messages = [{"role": "system", "content": prompt}]
            response = await llm_service.generate(
                messages=messages,
                temperature=0.8,
                max_tokens=100,
            )
            
            accept_message = response.content.strip()
            if accept_message and len(accept_message) > 5:
                return accept_message
        
        except Exception as e:
            logger.error(f"Failed to generate accept message: {e}")
        
        return "好的，让我给你拍张照片~"
    
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
        
        if parts:
            return " ".join(parts)
        
        return "friendly and warm"


image_intent_handler = ImageIntentHandler()
