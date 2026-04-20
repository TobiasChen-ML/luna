import logging
from typing import Optional, Union
import numpy as np

from ..core.config import get_settings

logger = logging.getLogger(__name__)

_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        settings = get_settings()
        model_name = getattr(settings, 'embedding_model', 'all-MiniLM-L6-v2')
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer(model_name)
            logger.info(f"Loaded embedding model: {model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, using random embeddings")
            _embedding_model = None
    return _embedding_model


class EmbeddingService:
    def __init__(self, model_name: Optional[str] = None, cache_size: int = 1000):
        self.settings = get_settings()
        self._model_name = model_name or getattr(self.settings, 'embedding_model', 'all-MiniLM-L6-v2')
        self._model = None
        self._embedding_dim = 384
        self._cache: dict[str, list[float]] = {}
        self._cache_size = cache_size
        self._provider = getattr(self.settings, 'embedding_provider', 'local')

    def _get_model(self):
        if self._model is None:
            if self._provider == 'local':
                try:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(self._model_name)
                    self._embedding_dim = self._model.get_sentence_embedding_dimension()
                    logger.info(f"Loaded local embedding model: {self._model_name}, dim={self._embedding_dim}")
                except ImportError:
                    logger.warning("sentence-transformers not installed")
                    self._model = None
            elif self._provider == 'openai':
                self._embedding_dim = 1536
        return self._model

    @property
    def embedding_dim(self) -> int:
        return self._embedding_dim

    def _get_cache_key(self, text: str) -> str:
        return hash(text)

    def _update_cache(self, text: str, embedding: list[float]):
        if len(self._cache) >= self._cache_size:
            oldest_keys = list(self._cache.keys())[:self._cache_size // 2]
            for key in oldest_keys:
                del self._cache[key]
        self._cache[self._get_cache_key(text)] = embedding

    async def embed(self, text: str) -> list[float]:
        if not text or not text.strip():
            return [0.0] * self._embedding_dim

        cache_key = self._get_cache_key(text)
        if cache_key in self._cache:
            return self._cache[cache_key]

        embedding = await self._generate_embedding(text)
        self._update_cache(text, embedding)
        return embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = []
        for text in texts:
            emb = await self.embed(text)
            results.append(emb)
        return results

    async def _generate_embedding(self, text: str) -> list[float]:
        provider = self._provider

        if provider == 'local':
            return await self._embed_local(text)
        elif provider == 'openai':
            return await self._embed_openai(text)
        elif provider == 'cloudflare':
            return await self._embed_cloudflare(text)
        else:
            logger.warning(f"Unknown embedding provider: {provider}, using local")
            return await self._embed_local(text)

    async def _embed_local(self, text: str) -> list[float]:
        model = self._get_model()
        if model is not None:
            try:
                embedding = model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Local embedding failed: {e}")

        logger.warning("Using random embedding fallback")
        dummy = np.random.randn(self._embedding_dim).astype(np.float32)
        dummy = dummy / np.linalg.norm(dummy)
        return dummy.tolist()

    async def _embed_openai(self, text: str) -> list[float]:
        settings = get_settings()
        api_key = getattr(settings, 'openai_api_key', None) or getattr(settings, 'llm_api_key', None)

        if not api_key:
            logger.warning("OpenAI API key not set, using random embedding")
            return await self._embed_local(text)

        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"input": text, "model": "text-embedding-3-small"}
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["data"][0]["embedding"]
                else:
                    logger.error(f"OpenAI embedding failed: {response.status_code}")
                    return await self._embed_local(text)
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            return await self._embed_local(text)

    async def _embed_cloudflare(self, text: str) -> list[float]:
        settings = get_settings()
        account_id = getattr(settings, 'cf_account_id', None)
        api_token = getattr(settings, 'cf_api_token', None)

        if not account_id or not api_token:
            logger.warning("Cloudflare credentials not set, using local embedding")
            return await self._embed_local(text)

        try:
            import httpx
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/baai/bge-base-en-v1.5",
                    headers={"Authorization": f"Bearer {api_token}"},
                    json={"text": [text]}
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") and data.get("result"):
                        return data["result"][0]
                    else:
                        logger.error(f"Cloudflare embedding failed: {data.get('errors')}")
                else:
                    logger.error(f"Cloudflare embedding request failed: {response.status_code}")

            return await self._embed_local(text)
        except Exception as e:
            logger.error(f"Cloudflare embedding error: {e}")
            return await self._embed_local(text)

    def embed_sync(self, text: str) -> list[float]:
        model = self._get_model()
        if model is not None:
            try:
                embedding = model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Sync embedding failed: {e}")

        dummy = np.random.randn(self._embedding_dim).astype(np.float32)
        dummy = dummy / np.linalg.norm(dummy)
        return dummy.tolist()

    def clear_cache(self):
        self._cache.clear()

    async def health_check(self) -> dict:
        model = self._get_model()
        return {
            "status": "healthy" if model is not None else "fallback",
            "provider": self._provider,
            "model": self._model_name,
            "embedding_dim": self._embedding_dim,
            "cache_size": len(self._cache),
        }


embedding_service = EmbeddingService()
