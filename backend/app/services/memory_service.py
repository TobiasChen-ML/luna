import logging
import uuid
import json
import math
from datetime import datetime, timedelta
from typing import Optional, Any
import numpy as np

from ..core.config import get_settings
from ..core.database import db
from .redis_service import RedisService
from .llm_service import LLMService
from .embedding_service import EmbeddingService, embedding_service
from .vector_store import memory_vector_store, global_memory_vector_store

logger = logging.getLogger(__name__)


class MemoryService:
    MEMORY_LAYERS = ["working", "episodic", "semantic"]
    
    WORKING_MEMORY_TTL = 3600
    EPISODIC_MEMORY_LIMIT = 100
    SEMANTIC_MEMORY_LIMIT = 50
    
    DEFAULT_DECAY_RATE = 0.05
    
    def __init__(
        self,
        redis: Optional[RedisService] = None,
        llm: Optional[LLMService] = None,
        embedding_svc: Optional[EmbeddingService] = None,
        use_vector_store: bool = True,
    ):
        self.settings = get_settings()
        self.redis = redis
        self.llm = llm
        self._embedding_svc = embedding_svc or embedding_service
        self._use_vector_store = use_vector_store and getattr(self.settings, 'vector_search_enabled', True)
        self._decay_rate = getattr(self.settings, 'memory_decay_rate', self.DEFAULT_DECAY_RATE)

    async def _get_redis(self) -> RedisService:
        if self.redis is None:
            self.redis = RedisService()
        return self.redis

    async def _get_llm(self) -> LLMService:
        if self.llm is None:
            self.llm = LLMService.get_instance()
        return self.llm

    def calculate_decayed_importance(
        self, 
        importance: int, 
        last_accessed: Optional[datetime],
        decay_rate: Optional[float] = None
    ) -> float:
        """
        Calculate time-decayed importance.
        Formula: decayed = importance * exp(-decay_rate * days_since_access)
        With decay_rate=0.05, half-life is approximately 14 days.
        """
        if last_accessed is None:
            return float(importance)
        
        decay = decay_rate or self._decay_rate
        now = datetime.utcnow()
        days_since_access = (now - last_accessed).total_seconds() / 86400
        
        decayed = importance * math.exp(-decay * days_since_access)
        return max(decayed, 0.1)

    async def get_context(self, character_id: str, user_id: str) -> dict:
        working_memory = await self._get_working_memory(user_id, character_id)
        episodic_summary = await self._get_episodic_summary(user_id, character_id)
        semantic_facts = await self._get_semantic_facts(user_id, character_id)
        global_memories = await self._get_global_memories(user_id)
        
        return {
            "character_id": character_id,
            "user_id": user_id,
            "working_memory": working_memory,
            "episodic_summary": episodic_summary,
            "semantic_facts": semantic_facts,
            "global_memories": global_memories,
        }

    async def _get_working_memory(self, user_id: str, character_id: str) -> list[dict]:
        key = f"working_memory:{user_id}:{character_id}"
        
        try:
            redis = await self._get_redis()
            cached = await redis.get_json(key)
            if cached:
                return cached.get("memories", [])
        except Exception as e:
            logger.warning(f"Redis unavailable for working memory, using empty: {e}")
        
        return []

    async def _get_episodic_summary(self, user_id: str, character_id: str) -> Optional[str]:
        key = f"episodic_summary:{user_id}:{character_id}"
        
        try:
            redis = await self._get_redis()
            cached = await redis.get_json(key)
            if cached:
                return cached.get("summary")
        except Exception as e:
            logger.warning(f"Redis unavailable for episodic summary: {e}")
        
        rows = await db.execute(
            """
            SELECT content, importance, last_accessed 
            FROM memories 
            WHERE user_id = ? AND character_id = ? AND layer = 'episodic'
            ORDER BY decayed_importance DESC, created_at DESC
            LIMIT 10
            """,
            (user_id, character_id),
            fetch_all=True
        )
        
        if not rows:
            return None
        
        memory_texts = [row["content"] for row in rows]
        summary = await self._summarize_memories(memory_texts)
        
        try:
            redis = await self._get_redis()
            await redis.set_json(key, {"summary": summary}, ex=86400)
        except Exception:
            pass
        
        return summary

    async def _get_semantic_facts(self, user_id: str, character_id: str) -> list[str]:
        key = f"semantic_facts:{user_id}:{character_id}"
        
        try:
            redis = await self._get_redis()
            cached = await redis.get_json(key)
            if cached:
                return cached.get("facts", [])
        except Exception as e:
            logger.warning(f"Redis unavailable for semantic facts: {e}")
        
        rows = await db.execute(
            """
            SELECT content 
            FROM memories 
            WHERE user_id = ? AND character_id = ? AND layer = 'semantic'
            ORDER BY decayed_importance DESC, created_at DESC
            LIMIT ?
            """,
            (user_id, character_id, self.SEMANTIC_MEMORY_LIMIT),
            fetch_all=True
        )
        
        facts = [row["content"] for row in rows]
        
        try:
            redis = await self._get_redis()
            await redis.set_json(key, {"facts": facts}, ex=86400)
        except Exception:
            pass
        
        return facts

    async def _get_global_memories(self, user_id: str) -> list[dict]:
        rows = await db.execute(
            """
            SELECT id, content, category, source_character_id, confidence, 
                   reference_count, is_confirmed, created_at, last_accessed
            FROM global_memories 
            WHERE user_id = ?
            ORDER BY reference_count DESC, confidence DESC
            """,
            (user_id,),
            fetch_all=True
        )
        
        return [
            {
                "id": row["id"],
                "content": row["content"],
                "category": row["category"],
                "source_character_id": row["source_character_id"],
                "confidence": row["confidence"],
                "reference_count": row["reference_count"],
                "is_confirmed": bool(row["is_confirmed"]),
                "created_at": row["created_at"],
                "last_accessed": row["last_accessed"],
            }
            for row in rows
        ]

    async def add_memory(
        self,
        user_id: str,
        character_id: str,
        content: str,
        layer: str = "episodic",
        importance: int = 5,
        metadata: Optional[dict] = None,
    ) -> dict:
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        importance = max(1, min(10, importance))
        decayed_importance = float(importance)
        
        embedding = await self._generate_embedding(content)
        embedding_blob = embedding.tobytes() if embedding is not None else None
        
        await db.execute(
            """
            INSERT INTO memories 
            (id, user_id, character_id, content, layer, embedding, metadata, 
             importance, decayed_importance, last_accessed, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                memory_id, user_id, character_id, content, layer, embedding_blob,
                json.dumps(metadata or {}), importance, decayed_importance, now, now, now
            )
        )
        
        if self._use_vector_store and embedding is not None:
            try:
                await memory_vector_store.add_memory(
                    memory_id=memory_id,
                    embedding=embedding.tolist(),
                    content=content,
                    user_id=user_id,
                    character_id=character_id,
                    layer=layer,
                    importance=importance,
                )
            except Exception as e:
                logger.warning(f"Failed to add memory to vector store: {e}")
        
        if layer == "working":
            await self._add_to_working_memory(user_id, character_id, memory_id, content)
        
        await self._invalidate_cache(user_id, character_id)
        
        return {"memory_id": memory_id, "layer": layer, "importance": importance}

    async def _add_to_working_memory(
        self,
        user_id: str,
        character_id: str,
        memory_id: str,
        content: str,
    ):
        key = f"working_memory:{user_id}:{character_id}"
        
        try:
            redis = await self._get_redis()
            cached = await redis.get_json(key) or {"memories": []}
            
            memories = cached.get("memories", [])
            memories.insert(0, {
                "id": memory_id,
                "content": content,
                "created_at": datetime.utcnow().isoformat(),
            })
            
            memories = memories[:20]
            
            await redis.set_json(key, {"memories": memories}, ex=self.WORKING_MEMORY_TTL)
        except Exception as e:
            logger.warning(f"Could not add to working memory in Redis: {e}")

    async def update_memory_access(self, memory_id: str) -> None:
        """
        Update last_accessed timestamp and recalculate decayed_importance.
        Should be called when memory is retrieved or referenced.
        """
        row = await db.execute(
            "SELECT importance, last_accessed FROM memories WHERE id = ?",
            (memory_id,),
            fetch=True
        )
        
        if not row:
            return
        
        now = datetime.utcnow()
        decayed = self.calculate_decayed_importance(row["importance"], row["last_accessed"])
        
        await db.execute(
            """
            UPDATE memories 
            SET last_accessed = ?, decayed_importance = ?, updated_at = ?
            WHERE id = ?
            """,
            (now, decayed, now, memory_id)
        )

    async def query_memories(
        self,
        user_id: str,
        character_id: str,
        query: str,
        layer: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        query_embedding = await self._generate_embedding(query)
        
        if self._use_vector_store and query_embedding is not None:
            try:
                vector_results = await memory_vector_store.search_memories(
                    query_embedding=query_embedding.tolist(),
                    user_id=user_id,
                    character_id=character_id,
                    layer=layer,
                    n_results=limit * 2,
                )
                
                if vector_results:
                    memory_ids = [r["id"] for r in vector_results]
                    placeholders = ",".join("?" * len(memory_ids))
                    rows = await db.execute(
                        f"""
                        SELECT id, content, layer, importance, decayed_importance, created_at
                        FROM memories WHERE id IN ({placeholders})
                        """,
                        tuple(memory_ids),
                        fetch_all=True
                    )
                    rows_by_id = {r["id"]: r for r in rows}
                    
                    results = []
                    for vr in vector_results:
                        row = rows_by_id.get(vr["id"])
                        if row:
                            decayed = row["decayed_importance"]
                            combined_score = 0.6 * vr["similarity"] + 0.4 * (decayed / 10.0)
                            results.append({
                                "id": row["id"],
                                "content": row["content"],
                                "layer": row["layer"],
                                "importance": row["importance"],
                                "decayed_importance": decayed,
                                "created_at": row["created_at"],
                                "similarity": vr["similarity"],
                                "combined_score": combined_score,
                            })
                    
                    results.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
                    return results[:limit]
            except Exception as e:
                logger.warning(f"Vector search failed, falling back to SQLite: {e}")
        
        if query_embedding is None:
            base_query = """
                SELECT id, content, layer, importance, decayed_importance, 
                       last_accessed, created_at
                FROM memories 
                WHERE user_id = ? AND character_id = ?
            """
            params = [user_id, character_id]
            
            if layer:
                base_query += " AND layer = ?"
                params.append(layer)
            
            base_query += " ORDER BY decayed_importance DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            rows = await db.execute(base_query, tuple(params), fetch_all=True)
            
            return [
                {
                    "id": row["id"],
                    "content": row["content"],
                    "layer": row["layer"],
                    "importance": row["importance"],
                    "decayed_importance": row["decayed_importance"],
                    "created_at": row["created_at"],
                    "similarity": None,
                }
                for row in rows
            ]
        
        base_query = """
            SELECT id, content, layer, embedding, importance, decayed_importance,
                   last_accessed, created_at
            FROM memories 
            WHERE user_id = ? AND character_id = ?
        """
        params = [user_id, character_id]
        
        if layer:
            base_query += " AND layer = ?"
            params.append(layer)
        
        base_query += " LIMIT 100"
        
        rows = await db.execute(base_query, tuple(params), fetch_all=True)
        
        scored_memories = []
        for row in rows:
            if row["embedding"]:
                mem_embedding = np.frombuffer(row["embedding"], dtype=np.float32)
                similarity = np.dot(query_embedding, mem_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(mem_embedding)
                )
                combined_score = 0.6 * similarity + 0.4 * (row["decayed_importance"] / 10.0)
                scored_memories.append((row, combined_score, similarity))
            else:
                scored_memories.append((row, row["decayed_importance"] / 10.0, None))
        
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        return [
            {
                "id": m["id"],
                "content": m["content"],
                "layer": m["layer"],
                "importance": m["importance"],
                "decayed_importance": m["decayed_importance"],
                "created_at": m["created_at"],
                "similarity": float(sim) if sim is not None else None,
            }
            for m, score, sim in scored_memories[:limit]
        ]

    async def forget_memories(self, user_id: str, character_id: str, memory_ids: list[str]) -> dict:
        placeholders = ",".join("?" * len(memory_ids))
        params = tuple(memory_ids) + (user_id,)
        
        result = await db.execute(
            f"DELETE FROM memories WHERE id IN ({placeholders}) AND user_id = ?",
            params
        )
        
        if self._use_vector_store:
            try:
                await memory_vector_store.delete_batch(memory_ids)
            except Exception as e:
                logger.warning(f"Failed to delete from vector store: {e}")
        
        await self._invalidate_cache(user_id, character_id)
        
        return {"deleted_count": result if result else 0}

    async def correct_memory(
        self,
        user_id: str,
        character_id: str,
        memory_id: str,
        new_content: str,
    ) -> dict:
        row = await db.execute(
            "SELECT id, layer, importance FROM memories WHERE id = ? AND user_id = ?",
            (memory_id, user_id),
            fetch=True
        )
        
        if not row:
            raise ValueError("Memory not found")
        
        now = datetime.utcnow()
        
        embedding = await self._generate_embedding(new_content)
        embedding_blob = embedding.tobytes() if embedding is not None else None
        
        await db.execute(
            """
            UPDATE memories 
            SET content = ?, embedding = ?, updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (new_content, embedding_blob, now, memory_id, user_id)
        )
        
        if self._use_vector_store and embedding is not None:
            try:
                await memory_vector_store.update(
                    id=memory_id,
                    embedding=embedding.tolist(),
                    content=new_content,
                    metadata={
                        "user_id": user_id,
                        "character_id": character_id,
                        "layer": row["layer"],
                        "importance": row["importance"],
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to update vector store: {e}")
        
        await self._invalidate_cache(user_id, character_id)
        
        return {"memory_id": memory_id, "content": new_content}

    async def extract_and_store(
        self,
        user_id: str,
        character_id: str,
        conversation: list[dict],
    ) -> list[dict]:
        extraction_prompt = f"""Analyze the conversation and extract important memories.
Return a JSON array of memory objects with 'content', 'layer' (working/episodic/semantic), and 'importance' (1-10).

Conversation:
{json.dumps(conversation, indent=2)}

Extract memories that capture:
1. User preferences and facts (semantic)
2. Important events or interactions (episodic)
3. Recent context that should be remembered (working)

Return JSON array only."""

        llm = await self._get_llm()
        
        result = await llm.generate_structured(
            [{"role": "user", "content": extraction_prompt}],
            schema={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "layer": {"type": "string"},
                        "importance": {"type": "number"},
                    },
                },
            },
        )
        
        stored_memories = []
        for mem in result.get("data", []):
            if mem.get("importance", 0) >= 5:
                stored = await self.add_memory(
                    user_id=user_id,
                    character_id=character_id,
                    content=mem["content"],
                    layer=mem.get("layer", "episodic"),
                    importance=mem.get("importance", 5),
                )
                stored_memories.append(stored)
        
        return stored_memories

    async def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        try:
            embedding_list = await self._embedding_svc.embed(text)
            if embedding_list:
                return np.array(embedding_list, dtype=np.float32)
            return None
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None

    async def _summarize_memories(self, memories: list[str]) -> str:
        if not memories:
            return ""
        
        prompt = f"""Summarize these memories into a concise narrative:

{chr(10).join(f'- {m}' for m in memories)}

Provide a brief summary."""

        llm = await self._get_llm()
        result = await llm.generate([{"role": "user", "content": prompt}], max_tokens=200)
        return result.content

    async def _invalidate_cache(self, user_id: str, character_id: str):
        keys = [
            f"working_memory:{user_id}:{character_id}",
            f"episodic_summary:{user_id}:{character_id}",
            f"semantic_facts:{user_id}:{character_id}",
        ]
        
        try:
            redis = await self._get_redis()
            for key in keys:
                await redis.delete(key)
        except Exception as e:
            logger.warning(f"Could not invalidate cache: {e}")

    async def index_memory(self, user_id: str, character_id: str, content: str, metadata: Optional[dict] = None) -> dict:
        return await self.add_memory(user_id, character_id, content, "semantic", metadata=metadata)

    async def get_memory_stats(self, user_id: str) -> dict:
        total_row = await db.execute(
            "SELECT COUNT(*) as count FROM memories WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        total = total_row["count"] if total_row else 0
        
        by_layer = {}
        for layer in self.MEMORY_LAYERS:
            row = await db.execute(
                "SELECT COUNT(*) as count FROM memories WHERE user_id = ? AND layer = ?",
                (user_id, layer),
                fetch=True
            )
            by_layer[layer] = row["count"] if row else 0
        
        global_row = await db.execute(
            "SELECT COUNT(*) as count FROM global_memories WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        global_count = global_row["count"] if global_row else 0
        
        return {
            "total": total,
            "by_layer": by_layer,
            "global_memories": global_count,
        }

    async def health_check(self) -> dict:
        return {"status": "healthy", "layers": self.MEMORY_LAYERS}

    async def suggest_global_memories(self, user_id: str) -> list[dict]:
        """
        Suggest memories that could be promoted to global based on:
        1. High importance (>= 7)
        2. Semantic layer
        3. Similar content appearing across multiple characters
        """
        rows = await db.execute(
            """
            SELECT m.content, m.character_id, m.importance, 
                   COUNT(*) as occurrence_count
            FROM memories m
            WHERE m.user_id = ? 
              AND m.layer = 'semantic'
              AND m.importance >= 7
            GROUP BY m.content
            HAVING occurrence_count >= 1
            ORDER BY m.importance DESC, occurrence_count DESC
            LIMIT 10
            """,
            (user_id,),
            fetch_all=True
        )
        
        suggestions = []
        for row in rows:
            existing = await db.execute(
                "SELECT id FROM global_memories WHERE user_id = ? AND content = ?",
                (user_id, row["content"]),
                fetch=True
            )
            
            if not existing:
                suggestions.append({
                    "content": row["content"],
                    "category": "preference",
                    "source_character_id": row["character_id"],
                    "occurrence_count": row["occurrence_count"],
                    "suggested_confidence": min(1.0, row["importance"] / 10.0),
                })
        
        return suggestions

    async def promote_to_global(
        self,
        user_id: str,
        memory_id: str,
        category: str = "preference",
    ) -> dict:
        """
        Promote a character-specific memory to global memory.
        """
        row = await db.execute(
            "SELECT content, character_id, importance FROM memories WHERE id = ? AND user_id = ?",
            (memory_id, user_id),
            fetch=True
        )
        
        if not row:
            raise ValueError("Memory not found")
        
        existing = await db.execute(
            "SELECT id FROM global_memories WHERE user_id = ? AND content = ?",
            (user_id, row["content"]),
            fetch=True
        )
        
        if existing:
            await db.execute(
                """
                UPDATE global_memories 
                SET reference_count = reference_count + 1, last_accessed = ?
                WHERE id = ?
                """,
                (datetime.utcnow(), existing["id"])
            )
            return {"global_memory_id": existing["id"], "status": "updated"}
        
        global_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        await db.execute(
            """
            INSERT INTO global_memories 
            (id, user_id, content, category, source_character_id, confidence, 
             reference_count, is_confirmed, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                global_id, user_id, row["content"], category, row["character_id"],
                min(1.0, row["importance"] / 10.0), 1, 0, now, now
            )
        )
        
        return {"global_memory_id": global_id, "status": "created"}

    async def create_global_memory(
        self,
        user_id: str,
        content: str,
        category: str = "preference",
        source_character_id: Optional[str] = None,
        confidence: float = 1.0,
    ) -> dict:
        """
        Create a new global memory directly.
        """
        global_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        await db.execute(
            """
            INSERT INTO global_memories 
            (id, user_id, content, category, source_character_id, confidence,
             reference_count, is_confirmed, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                global_id, user_id, content, category, source_character_id,
                confidence, 1, 0, now, now
            )
        )
        
        return {"global_memory_id": global_id, "content": content, "category": category}

    async def confirm_global_memory(self, user_id: str, global_memory_id: str) -> dict:
        """
        Mark a global memory as confirmed by the user.
        """
        await db.execute(
            "UPDATE global_memories SET is_confirmed = 1 WHERE id = ? AND user_id = ?",
            (global_memory_id, user_id)
        )
        
        return {"global_memory_id": global_memory_id, "confirmed": True}

    async def delete_global_memory(self, user_id: str, global_memory_id: str) -> dict:
        """
        Delete a global memory.
        """
        await db.execute(
            "DELETE FROM global_memories WHERE id = ? AND user_id = ?",
            (global_memory_id, user_id)
        )
        
        return {"deleted": True, "global_memory_id": global_memory_id}

    async def update_all_decayed_importance(self) -> int:
        """
        Batch update decayed_importance for all memories.
        Should be called periodically (e.g., daily via cron).
        """
        rows = await db.execute(
            "SELECT id, importance, last_accessed FROM memories",
            fetch_all=True
        )
        
        updated = 0
        now = datetime.utcnow()
        
        for row in rows:
            last_accessed = row["last_accessed"]
            if isinstance(last_accessed, str):
                try:
                    last_accessed = datetime.fromisoformat(last_accessed.replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    last_accessed = None
            
            decayed = self.calculate_decayed_importance(
                row["importance"], 
                last_accessed
            )
            await db.execute(
                "UPDATE memories SET decayed_importance = ?, updated_at = ? WHERE id = ?",
                (decayed, now, row["id"])
            )
            updated += 1
        
        logger.info(f"Updated decayed_importance for {updated} memories")
        return updated
