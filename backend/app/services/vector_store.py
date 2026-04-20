import logging
from typing import Optional, Any
import uuid

from ..core.config import get_settings

logger = logging.getLogger(__name__)

_chroma_client = None
_memories_collection = None
_global_memories_collection = None


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        persist_dir = getattr(settings, 'chroma_persist_dir', './chroma_db')
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            _chroma_client = chromadb.PersistentClient(
                path=persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            logger.info(f"ChromaDB client initialized at {persist_dir}")
        except ImportError:
            logger.warning("chromadb not installed, vector search disabled")
            _chroma_client = None
    return _chroma_client


class VectorStore:
    def __init__(self, collection_name: str = "memories", persist_dir: Optional[str] = None):
        self.settings = get_settings()
        self._persist_dir = persist_dir or getattr(self.settings, 'chroma_persist_dir', './chroma_db')
        self._collection_name = collection_name
        self._client = None
        self._collection = None

    def _get_client(self):
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings as ChromaSettings
                self._client = chromadb.PersistentClient(
                    path=self._persist_dir,
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
            except ImportError:
                logger.warning("chromadb not installed")
                self._client = None
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            if client is not None:
                try:
                    self._collection = client.get_or_create_collection(
                        name=self._collection_name,
                        metadata={"hnsw:space": "cosine"}
                    )
                    logger.info(f"ChromaDB collection '{self._collection_name}' ready, count={self._collection.count()}")
                except Exception as e:
                    logger.error(f"Failed to create collection: {e}")
                    self._collection = None
        return self._collection

    async def add(
        self,
        id: str,
        embedding: list[float],
        content: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        collection = self._get_collection()
        if collection is None:
            logger.warning("Collection not available, skipping add")
            return False

        try:
            collection.add(
                ids=[id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata or {}]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add to vector store: {e}")
            return False

    async def add_batch(
        self,
        ids: list[str],
        embeddings: list[list[float]],
        contents: list[str],
        metadatas: Optional[list[dict]] = None,
    ) -> int:
        collection = self._get_collection()
        if collection is None:
            return 0

        try:
            collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas or [{} for _ in ids]
            )
            return len(ids)
        except Exception as e:
            logger.error(f"Failed to batch add: {e}")
            return 0

    async def search(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None,
    ) -> list[dict]:
        collection = self._get_collection()
        if collection is None:
            return []

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document,
                include=["documents", "metadatas", "distances"]
            )

            if not results or not results.get("ids"):
                return []

            items = []
            ids = results["ids"][0] if results["ids"] else []
            docs = results["documents"][0] if results["documents"] else []
            metas = results["metadatas"][0] if results["metadatas"] else []
            dists = results["distances"][0] if results["distances"] else []

            for i, id_ in enumerate(ids):
                similarity = 1.0 - (dists[i] if i < len(dists) else 0.5)
                items.append({
                    "id": id_,
                    "content": docs[i] if i < len(docs) else "",
                    "metadata": metas[i] if i < len(metas) else {},
                    "similarity": similarity,
                })

            return items
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def search_by_user_character(
        self,
        query_embedding: list[float],
        user_id: str,
        character_id: str,
        n_results: int = 10,
    ) -> list[dict]:
        return await self.search(
            query_embedding=query_embedding,
            n_results=n_results,
            where={"user_id": user_id, "character_id": character_id}
        )

    async def delete(self, id: str) -> bool:
        collection = self._get_collection()
        if collection is None:
            return False

        try:
            collection.delete(ids=[id])
            return True
        except Exception as e:
            logger.error(f"Failed to delete from vector store: {e}")
            return False

    async def delete_batch(self, ids: list[str]) -> int:
        collection = self._get_collection()
        if collection is None:
            return 0

        try:
            collection.delete(ids=ids)
            return len(ids)
        except Exception as e:
            logger.error(f"Failed to batch delete: {e}")
            return 0

    async def delete_by_user(self, user_id: str) -> int:
        collection = self._get_collection()
        if collection is None:
            return 0

        try:
            collection.delete(where={"user_id": user_id})
            return 1
        except Exception as e:
            logger.error(f"Failed to delete by user: {e}")
            return 0

    async def update(
        self,
        id: str,
        embedding: list[float],
        content: str,
        metadata: Optional[dict] = None,
    ) -> bool:
        collection = self._get_collection()
        if collection is None:
            return False

        try:
            collection.update(
                ids=[id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata or {}]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update in vector store: {e}")
            return False

    async def get(self, id: str) -> Optional[dict]:
        collection = self._get_collection()
        if collection is None:
            return None

        try:
            results = collection.get(ids=[id], include=["documents", "metadatas", "embeddings"])
            if results and results.get("ids"):
                return {
                    "id": results["ids"][0],
                    "content": results["documents"][0] if results["documents"] else "",
                    "metadata": results["metadatas"][0] if results["metadatas"] else {},
                    "embedding": results["embeddings"][0] if results["embeddings"] else None,
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get from vector store: {e}")
            return None

    async def count(self) -> int:
        collection = self._get_collection()
        if collection is None:
            return 0
        return collection.count()

    async def health_check(self) -> dict:
        collection = self._get_collection()
        if collection is None:
            return {
                "status": "unavailable",
                "collection": self._collection_name,
                "persist_dir": self._persist_dir,
                "count": 0,
            }

        return {
            "status": "healthy",
            "collection": self._collection_name,
            "persist_dir": self._persist_dir,
            "count": collection.count(),
        }

    async def clear(self) -> bool:
        client = self._get_client()
        if client is None:
            return False

        try:
            client.delete_collection(self._collection_name)
            self._collection = None
            self._collection = client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False


class MemoryVectorStore(VectorStore):
    def __init__(self):
        super().__init__(collection_name="memories")

    async def add_memory(
        self,
        memory_id: str,
        embedding: list[float],
        content: str,
        user_id: str,
        character_id: str,
        layer: str = "episodic",
        importance: int = 5,
    ) -> bool:
        metadata = {
            "user_id": user_id,
            "character_id": character_id,
            "layer": layer,
            "importance": importance,
        }
        return await self.add(memory_id, embedding, content, metadata)

    async def search_memories(
        self,
        query_embedding: list[float],
        user_id: str,
        character_id: str,
        layer: Optional[str] = None,
        n_results: int = 10,
    ) -> list[dict]:
        where = {"user_id": user_id, "character_id": character_id}
        if layer:
            where["layer"] = layer

        results = await self.search(query_embedding, n_results=n_results, where=where)

        for item in results:
            item["importance"] = item.get("metadata", {}).get("importance", 5)
            item["layer"] = item.get("metadata", {}).get("layer", "episodic")

        return results


class GlobalMemoryVectorStore(VectorStore):
    def __init__(self):
        super().__init__(collection_name="global_memories")

    async def add_global_memory(
        self,
        memory_id: str,
        embedding: list[float],
        content: str,
        user_id: str,
        category: str = "preference",
    ) -> bool:
        metadata = {
            "user_id": user_id,
            "category": category,
        }
        return await self.add(memory_id, embedding, content, metadata)

    async def search_global_memories(
        self,
        query_embedding: list[float],
        user_id: str,
        n_results: int = 10,
    ) -> list[dict]:
        results = await self.search(
            query_embedding,
            n_results=n_results,
            where={"user_id": user_id}
        )

        for item in results:
            item["category"] = item.get("metadata", {}).get("category", "preference")

        return results


memory_vector_store = MemoryVectorStore()
global_memory_vector_store = GlobalMemoryVectorStore()