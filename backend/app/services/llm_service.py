import json
import logging
from typing import Optional, AsyncIterator, Any
from ..core.config import get_settings, get_config_value
from .llm import LLMRequest, LLMResponse, StructuredResponse, Message, BaseLLMProvider
from .llm.providers import NovitaLLMProvider

logger = logging.getLogger(__name__)


class LLMService:
    _instance = None
    
    def __init__(self):
        self.settings = get_settings()
        self._providers: dict[str, Any] = {}
        self._init_providers()
    
    @classmethod
    def get_instance(cls) -> "LLMService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _init_providers(self):
        # Prefer explicit NOVITA_API_KEY, but accept LLM_API_KEY for compatibility.
        novita_key = self.settings.novita_api_key or self.settings.llm_api_key
        if novita_key:
            self._providers["novita"] = NovitaLLMProvider(
                api_key=novita_key,
                base_url=self.settings.llm_base_url,
                default_model=self.settings.llm_primary_model
            )
    
    async def refresh_providers(self) -> None:
        novita_key = await get_config_value("NOVITA_API_KEY", self.settings.novita_api_key)
        if not novita_key:
            novita_key = await get_config_value("LLM_API_KEY", self.settings.llm_api_key)
        llm_base_url = await get_config_value("LLM_BASE_URL", self.settings.llm_base_url)
        primary_model = await get_config_value("LLM_CHAT_MODEL", self.settings.llm_primary_model)

        new_providers: dict[str, Any] = {}
        if novita_key:
            new_providers["novita"] = NovitaLLMProvider(
                api_key=novita_key,
                base_url=llm_base_url,
                default_model=primary_model,
            )
        self._providers = new_providers
        logger.info("LLMService providers refreshed from config")

    async def get_provider(self, provider_name: Optional[str] = None) -> Optional[Any]:
        if provider_name:
            return self._providers.get(provider_name)
        
        provider_name = await get_config_value("LLM_PROVIDER", self.settings.llm_provider)
        return self._providers.get(provider_name)
    
    async def generate(
        self,
        messages: list[Message | dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        provider: Optional[str] = None
    ) -> LLMResponse:
        normalized_messages = []
        for m in messages:
            if isinstance(m, dict):
                normalized_messages.append(Message(**m))
            else:
                normalized_messages.append(m)
        
        request = LLMRequest(
            messages=normalized_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        prov = await self.get_provider(provider)
        if not prov:
            raise ValueError(f"Provider {provider or self.settings.llm_provider} not available")
        return await prov.generate(request)
    
    async def generate_stream(
        self,
        messages: list[Message | dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        provider: Optional[str] = None
    ) -> AsyncIterator[str]:
        normalized_messages = []
        for m in messages:
            if isinstance(m, dict):
                normalized_messages.append(Message(**m))
            else:
                normalized_messages.append(m)
        
        request = LLMRequest(
            messages=normalized_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        prov = await self.get_provider(provider)
        if not prov:
            raise ValueError(f"Provider {provider or self.settings.llm_provider} not available")
        
        try:
            async for chunk in prov.generate_stream(request):
                yield chunk
        except Exception as e:
            logger.error(f"Stream failed: {e}")
            if isinstance(e, IndexError):
                logger.warning("Falling back to non-stream response after stream IndexError")
                fallback_request = LLMRequest(
                    messages=normalized_messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False,
                )
                fallback_response = await prov.generate(fallback_request)
                if fallback_response.content:
                    yield fallback_response.content
                return
            raise
    
    async def generate_structured(
        self,
        messages: list[Message | dict],
        schema: dict,
        model: Optional[str] = None,
        temperature: float = 0.3,
        provider: Optional[str] = None
    ) -> StructuredResponse:
        normalized_messages = []
        for m in messages:
            if isinstance(m, dict):
                normalized_messages.append(Message(**m))
            else:
                normalized_messages.append(m)
        
        structured_model = model or await get_config_value(
            "LLM_INTENT_MODEL",
            self.settings.llm_structured_model,
        )

        request = LLMRequest(
            messages=normalized_messages,
            model=structured_model,
            temperature=temperature,
            max_tokens=1024
        )
        
        configured_provider = await get_config_value("LLM_PROVIDER", self.settings.llm_provider)
        preferred_name = provider or configured_provider

        preferred = await self.get_provider(preferred_name)
        if not preferred:
            raise ValueError("No LLM provider available")

        prov = preferred
        try:
            return await prov.generate_structured(request, schema)
        except Exception as e:
            logger.error(f"Structured generation failed on provider={preferred_name or 'default'}: {e}")
            raise
    
    async def detect_intent(self, user_message: str, context: Optional[dict] = None) -> dict:
        intent_schema = {
            "type": "object",
            "properties": {
                "intent": {"type": "string", "enum": ["chat", "image", "video", "audio", "tool", "system"]},
                "tone": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]},
                "action": {"type": "string"},
                "memory_hint": {"type": "string"},
                "tool_hint": {"type": "string"},
                "confidence": {"type": "number"}
            },
            "required": ["intent", "confidence"]
        }
        
        system_prompt = """Analyze the user message and determine:
1. The primary intent:
   - chat: Normal conversation
   - image: User wants an image generated
   - video: User wants a video generated
   - audio: User wants to HEAR the response spoken aloud (e.g., "say goodnight to me", "I want to hear your voice", "tell me with your voice", "read this to me", "speak to me")
   - tool: User wants to use a specific tool
   - system: System-level request (settings, preferences)

2. The tone of the message
3. Priority level (low/normal/high)
4. Any action hints
5. Memory-related hints
6. Tool usage hints

Respond with valid JSON only."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        response = await self.generate_structured(messages, intent_schema)
        return response.data
    
    async def detect_video_intent(self, user_message: str) -> dict:
        """
        Specifically detect if the message is requesting a video.
        
        More focused than general intent detection for faster verification.
        
        Returns:
            dict with keys:
            - is_video_request: bool - True if user is asking for a video
            - confidence: float (0-1) - Confidence level of the detection
            - video_type: str - Type of video request (optional)
            - reasoning: str - Brief explanation (optional)
        """
        video_intent_schema = {
            "type": "object",
            "properties": {
                "is_video_request": {"type": "boolean"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "video_type": {"type": "string", "enum": ["selfie", "action", "unclear"]},
                "reasoning": {"type": "string"}
            },
            "required": ["is_video_request", "confidence"]
        }
        
        system_prompt = """Determine if the user is requesting a VIDEO from the AI character.

A video request is when the user wants the character to:
- Create/send a video of themselves
- Record a video
- Make a selfie video
- Animate/create motion

NOT a video request:
- User talking about watching a video
- User discussing video content they saw elsewhere
- User asking about video features generally

Be strict - only mark as video request if clearly asking the character to create/send a video.

Respond with valid JSON only."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = await self.generate_structured(
                messages, 
                video_intent_schema,
                temperature=0.1,
                provider="novita"
            )
            return response.data
        except Exception as e:
            logger.error(f"Video intent detection failed: {e}")
            return {"is_video_request": False, "confidence": 0.0}
    
    async def detect_image_intent(self, user_message: str, context: Optional[dict] = None) -> dict:
        """
        Detect if the user is requesting an image generation.
        
        Returns:
            dict with keys:
            - is_image_request: bool - True if user wants an image
            - confidence: float (0-1) - Confidence level
            - prompt: str - Extracted prompt for image generation
            - style_hint: str - Style hints (optional)
            - lora_hint: str - LoRA/style hints (optional)
        """
        image_intent_schema = {
            "type": "object",
            "properties": {
                "is_image_request": {"type": "boolean"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "prompt": {"type": "string"},
                "style_hint": {"type": "string"},
                "lora_hint": {"type": "string"},
                "reasoning": {"type": "string"}
            },
            "required": ["is_image_request", "confidence"]
        }
        
        context_str = ""
        if context:
            context_str = f"\n\nContext: Character name is {context.get('character_name', 'the character')}."
        
        system_prompt = f"""Determine if the user is requesting an IMAGE to be generated.

An image request is when the user:
- Asks to see the character in a specific pose/scene
- Requests a photo/picture/selfie
- Describes a visual scene they want to see
- Uses phrases like "show me", "send me a picture", "take a photo"
- Describes what the character should be wearing/doing visually

NOT an image request:
- User describing themselves
- User talking about images they saw elsewhere
- General conversation about appearance

Extract a detailed image generation prompt if this is an image request.{context_str}

Respond with valid JSON only."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = await self.generate_structured(
                messages,
                image_intent_schema,
                temperature=0.1,
                provider="novita"
            )
            return response.data
        except Exception as e:
            logger.error(f"Image intent detection failed: {e}")
            return {"is_image_request": False, "confidence": 0.0}
    
    async def health_check(self) -> dict[str, bool]:
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.health_check()
            except Exception:
                results[name] = False
        return results
