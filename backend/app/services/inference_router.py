import logging
from typing import Optional, Any, AsyncIterator, Union

from ..core.config import get_settings
from .llm_service import LLMService
from .intent_router import intent_router, IntentType
from .local_inference import local_inference_service

logger = logging.getLogger(__name__)


class InferenceRouter:
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        use_intent_routing: bool = True,
    ):
        self.settings = get_settings()
        self._llm_service = llm_service
        self._use_intent_routing = use_intent_routing and getattr(
            self.settings, 'intent_routing_enabled', True
        )
        self._local_enabled = getattr(self.settings, 'local_inference_enabled', False)

    async def _get_llm_service(self) -> LLMService:
        if self._llm_service is None:
            self._llm_service = LLMService.get_instance()
        return self._llm_service

    async def generate(
        self,
        messages: list[dict],
        user_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        force_cloud: bool = False,
    ) -> dict:
        text_to_analyze = user_message or ""
        if not text_to_analyze and messages:
            last_msg = messages[-1]
            text_to_analyze = last_msg.get("content", "")

        use_local, intent, confidence = intent_router.should_use_local_model(text_to_analyze)

        if force_cloud or not self._local_enabled:
            use_local = False

        if use_local and not force_cloud:
            logger.info(f"Using local model for intent: {intent.value} (confidence: {confidence:.2f})")
            
            prompt = self._build_simple_prompt(messages)
            response = await local_inference_service.generate(
                prompt=prompt,
                max_tokens=min(max_tokens, 150),
                temperature=temperature,
            )
            
            return {
                "content": response,
                "model": "local",
                "intent": intent.value,
                "confidence": confidence,
                "provider": "local",
            }

        llm = await self._get_llm_service()
        result = await llm.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return {
            "content": result.content,
            "model": result.model,
            "intent": intent.value,
            "confidence": confidence,
            "provider": "cloud",
            "usage": result.usage,
        }

    async def generate_stream(
        self,
        messages: list[dict],
        user_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        force_cloud: bool = False,
    ) -> AsyncIterator[dict]:
        text_to_analyze = user_message or ""
        if not text_to_analyze and messages:
            last_msg = messages[-1]
            text_to_analyze = last_msg.get("content", "")

        use_local, intent, confidence = intent_router.should_use_local_model(text_to_analyze)

        if force_cloud or not self._local_enabled:
            use_local = False

        if use_local and not force_cloud:
            logger.info(f"Using local model stream for intent: {intent.value}")
            
            prompt = self._build_simple_prompt(messages)
            
            async for chunk in local_inference_service.generate_stream(
                prompt=prompt,
                max_tokens=min(max_tokens, 150),
                temperature=temperature,
            ):
                yield {
                    "content": chunk,
                    "model": "local",
                    "done": False,
                }
            
            yield {
                "content": "",
                "model": "local",
                "done": True,
                "intent": intent.value,
                "confidence": confidence,
            }
            return

        llm = await self._get_llm_service()
        
        async for chunk in llm.generate_stream(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield {
                "content": chunk,
                "model": "cloud",
                "done": False,
            }
        
        yield {
            "content": "",
            "model": "cloud",
            "done": True,
            "intent": intent.value,
            "confidence": confidence,
        }

    def _build_simple_prompt(self, messages: list[dict]) -> str:
        if messages:
            last_msg = messages[-1]
            return last_msg.get("content", "")
        return ""

    def get_route_info(self, text: str) -> dict:
        return intent_router.get_route_info(text)

    async def health_check(self) -> dict:
        local_health = await local_inference_service.health_check()
        
        return {
            "status": "healthy",
            "intent_routing_enabled": self._use_intent_routing,
            "local_inference_enabled": self._local_enabled,
            "local_model": local_health,
        }


inference_router = InferenceRouter()