import logging
import json
import httpx
from typing import Optional, Any, AsyncIterator
from datetime import datetime

from ..core.config import get_settings

logger = logging.getLogger(__name__)

LOCAL_MODEL_RESPONSES = {
    "greeting": {
        "zh": ["你好！今天过得怎么样？", "嗨！有什么想聊的吗？", "你好呀~"],
        "en": ["Hello! How are you today?", "Hi there! What would you like to talk about?", "Hey! Good to see you!"],
    },
    "simple_ack": {
        "zh": ["好的，我明白了。", "收到！继续吧~", "嗯嗯，明白了"],
        "en": ["Okay, I understand.", "Got it! Let's continue.", "Sure, I got that."],
    },
    "short_response": {
        "zh": ["确实如此。", "你说得对。", "我也这么觉得。"],
        "en": ["That's true.", "You're right.", "I agree with you."],
    },
}


class LocalInferenceService:
    def __init__(
        self,
        model_url: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 30,
    ):
        self.settings = get_settings()
        self._model_url = model_url or getattr(self.settings, 'local_model_url', 'http://localhost:11434')
        self._model_name = model_name or getattr(self.settings, 'local_model_name', 'qwen2.5:1.5b')
        self._timeout = timeout
        self._client = None
        self._enabled = getattr(self.settings, 'local_inference_enabled', False)
        self._cache: dict[str, str] = {}

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    def is_available(self) -> bool:
        return self._enabled and self._model_url and self._model_name

    async def check_health(self) -> bool:
        if not self.is_available():
            return False

        try:
            client = self._get_client()
            response = await client.get(f"{self._model_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Local model health check failed: {e}")
            return False

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
    ) -> str:
        if not self.is_available():
            return await self._fallback_response(prompt)

        cache_key = f"{prompt[:50]}:{max_tokens}:{temperature}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            client = self._get_client()
            
            response = await client.post(
                f"{self._model_url}/api/chat",
                json={
                    "model": self._model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                    },
                },
                timeout=self._timeout,
            )

            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "")
                
                if len(content) > 20:
                    self._cache[cache_key] = content
                
                return content
            else:
                logger.warning(f"Local model returned {response.status_code}")
                return await self._fallback_response(prompt)

        except httpx.TimeoutException:
            logger.warning("Local model timeout")
            return await self._fallback_response(prompt)
        except Exception as e:
            logger.error(f"Local inference failed: {e}")
            return await self._fallback_response(prompt)

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        if not self.is_available():
            yield await self._fallback_response(prompt)
            return

        try:
            client = self._get_client()
            
            async with client.stream(
                "POST",
                f"{self._model_url}/api/chat",
                json={
                    "model": self._model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                    },
                },
                timeout=self._timeout,
            ) as response:
                async for line in response.aiter_lines():
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            logger.error(f"Local stream inference failed: {e}")
            yield await self._fallback_response(prompt)

    async def _fallback_response(self, prompt: str) -> str:
        prompt_lower = prompt.lower().strip()
        
        greetings = ["hi", "hello", "hey", "你好", "嗨"]
        for g in greetings:
            if prompt_lower.startswith(g):
                return self._get_random_response("greeting")
        
        acks = ["ok", "yes", "sure", "好的", "是", "明白"]
        for a in acks:
            if prompt_lower.startswith(a):
                return self._get_random_response("simple_ack")
        
        return self._get_random_response("short_response")

    def _get_random_response(self, category: str) -> str:
        import random
        
        responses = LOCAL_MODEL_RESPONSES.get(category, LOCAL_MODEL_RESPONSES["short_response"])
        
        zh_responses = responses.get("zh", [])
        en_responses = responses.get("en", [])
        
        all_responses = zh_responses + en_responses
        if all_responses:
            return random.choice(all_responses)
        
        return "好的，我明白了。"

    async def generate_simple_greeting(self, language: str = "zh") -> str:
        import random
        
        responses = LOCAL_MODEL_RESPONSES.get("greeting", {})
        lang_responses = responses.get(language, responses.get("zh", ["你好！"]))
        
        return random.choice(lang_responses)

    async def health_check(self) -> dict:
        available = await self.check_health()
        
        return {
            "status": "healthy" if available else "unavailable",
            "enabled": self._enabled,
            "model_url": self._model_url,
            "model_name": self._model_name,
            "cache_size": len(self._cache),
        }


local_inference_service = LocalInferenceService()