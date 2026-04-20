import logging
import json
from typing import Optional
from datetime import datetime

from app.core.database import db
from app.models.character import (
    CharacterCreate,
    CharacterUpdate,
    CharacterResponse,
    CharacterDetailResponse,
    generate_character_id,
    generate_slug,
)

logger = logging.getLogger(__name__)

UGC_DEFAULT_REVIEW_STATUS = "approved"


class CharacterService:
    _instance = None
    
    def __init__(self):
        pass
    
    @classmethod
    def get_instance(cls) -> "CharacterService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def create_character(self, data: CharacterCreate) -> dict:
        character_id = generate_character_id()
        slug = data.slug or generate_slug(data.name)
        
        existing = await self.get_character_by_slug(slug)
        if existing:
            slug = f"{slug}-{character_id[-6:]}"
        
        now = datetime.utcnow().isoformat()
        
        character_data = {
            "id": character_id,
            "name": data.name,
            "first_name": data.first_name,
            "slug": slug,
            "description": data.description,
            "age": data.age,
            "gender": data.gender or "female",
            "ethnicity": data.ethnicity,
            "nationality": data.nationality,
            "occupation": data.occupation,
            "top_category": data.top_category or "girls",
            "sub_category": data.sub_category,
            "filter_tags": json.dumps(data.filter_tags) if data.filter_tags else None,
            "personality_tags": json.dumps(data.personality_tags) if data.personality_tags else None,
            "keywords": json.dumps(data.keywords) if data.keywords else None,
            "personality_summary": data.personality_summary,
            "personality_example": data.personality_example,
            "backstory": data.backstory,
            "system_prompt": data.system_prompt,
            "greeting": data.greeting,
            "avatar_url": data.avatar_url,
            "cover_url": data.cover_url,
            "avatar_card_url": data.avatar_card_url,
            "profile_image_url": data.profile_image_url,
            "preview_video_url": data.preview_video_url,
            "mature_image_url": data.mature_image_url,
            "mature_cover_url": data.mature_cover_url,
            "mature_video_url": data.mature_video_url,
            "voice_id": data.voice_id,
            "meta_title": data.meta_title,
            "meta_description": data.meta_description,
            "seo_optimized": 0,
            "is_official": 1,
            "is_public": 1 if data.is_public else 0,
            "template_id": data.template_id,
            "generation_mode": data.generation_mode or "manual",
            "popularity_score": 0.0,
            "chat_count": 0,
            "view_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        
        columns = ", ".join(character_data.keys())
        placeholders = ", ".join(["?" for _ in character_data])
        values = list(character_data.values())
        
        await db.execute(
            f"INSERT INTO characters ({columns}) VALUES ({placeholders})",
            tuple(values)
        )
        
        logger.info(f"Created character: {character_id} - {data.name}")
        
        return await self.get_character_by_id(character_id)
    
    async def get_character_by_id(self, character_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM characters WHERE id = ?",
            (character_id,),
            fetch=True
        )
        if row:
            return self._row_to_dict(row)
        return None
    
    async def get_character_by_slug(self, slug: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM characters WHERE slug = ?",
            (slug,),
            fetch=True
        )
        if row:
            return self._row_to_dict(row)
        return None
    
    async def list_characters(
        self,
        page: int = 1,
        page_size: int = 20,
        top_category: Optional[str] = None,
        is_official: Optional[bool] = None,
        is_public: Optional[bool] = None,
        search: Optional[str] = None,
        order_by: str = "created_at DESC",
    ) -> tuple[list[dict], int]:
        conditions = ["1=1"]
        params = []
        
        if top_category:
            conditions.append("top_category = ?")
            params.append(top_category)
        
        if is_official is not None:
            conditions.append("is_official = ?")
            params.append(1 if is_official else 0)
        
        if is_public is not None:
            conditions.append("is_public = ?")
            params.append(1 if is_public else 0)
        
        if search:
            conditions.append("(name LIKE ? OR description LIKE ? OR personality_summary LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        where_clause = " AND ".join(conditions)
        
        count_row = await db.execute(
            f"SELECT COUNT(*) as total FROM characters WHERE {where_clause}",
            tuple(params),
            fetch=True
        )
        total = count_row["total"] if count_row else 0
        
        offset = (page - 1) * page_size
        rows = await db.execute(
            f"SELECT * FROM characters WHERE {where_clause} ORDER BY {order_by} LIMIT ? OFFSET ?",
            tuple(params + [page_size, offset]),
            fetch_all=True
        )
        
        characters = [self._row_to_dict(row) for row in rows]
        
        return characters, total
    
    async def list_official_characters(
        self,
        top_category: Optional[str] = None,
        filter_tag: Optional[str] = None,
        page: int = 1,
        page_size: int = 24,
    ) -> tuple[list[dict], int]:
        conditions = ["is_official = 1", "is_public = 1", "lifecycle_status = 'active'"]
        params = []
        
        if top_category:
            conditions.append("top_category = ?")
            params.append(top_category)
        
        if filter_tag:
            conditions.append("(filter_tags LIKE ? OR personality_tags LIKE ?)")
            params.extend([f'%"{filter_tag}"%', f'%"{filter_tag}"%'])
        
        where_clause = " AND ".join(conditions)
        
        count_row = await db.execute(
            f"SELECT COUNT(*) as total FROM characters WHERE {where_clause}",
            tuple(params),
            fetch=True
        )
        total = count_row["total"] if count_row else 0
        
        offset = (page - 1) * page_size
        rows = await db.execute(
            f"SELECT * FROM characters WHERE {where_clause} ORDER BY popularity_score DESC, created_at DESC LIMIT ? OFFSET ?",
            tuple(params + [page_size, offset]),
            fetch_all=True
        )
        
        characters = [self._row_to_dict(row) for row in rows]
        
        return characters, total
    
    async def discover_characters(
        self,
        top_category: str = "girls",
        filter_tag: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 24,
        offset: int = 0,
    ) -> list[dict]:
        conditions = ["is_official = 1", "is_public = 1", "lifecycle_status = 'active'"]
        params = []
        
        if top_category:
            conditions.append("top_category = ?")
            params.append(top_category)
        
        if filter_tag:
            conditions.append("(filter_tags LIKE ? OR personality_tags LIKE ?)")
            params.extend([f'%"{filter_tag}"%', f'%"{filter_tag}"%'])
        
        if search:
            conditions.append("(name LIKE ? OR first_name LIKE ? OR description LIKE ? OR personality_summary LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term, search_term])
        
        where_clause = " AND ".join(conditions)
        
        rows = await db.execute(
            f"SELECT * FROM characters WHERE {where_clause} ORDER BY popularity_score DESC, created_at DESC LIMIT ? OFFSET ?",
            tuple(params + [limit, offset]),
            fetch_all=True
        )
        
        return [self._row_to_dict(row) for row in rows]
    
    async def update_character(self, character_id: str, data: CharacterUpdate) -> Optional[dict]:
        existing = await self.get_character_by_id(character_id)
        if not existing:
            return None
        
        updates = []
        params = []
        
        update_fields = [
            "name", "first_name", "slug", "description", "age", "gender",
            "top_category", "sub_category", "personality_summary", "personality_example",
            "backstory", "system_prompt", "greeting", "avatar_url", "cover_url",
            "avatar_card_url", "profile_image_url", "preview_video_url",
            "mature_image_url", "mature_cover_url", "mature_video_url",
            "voice_id", "meta_title", "meta_description", "seo_optimized",
            "is_public", "lifecycle_status"
        ]
        
        for field in update_fields:
            value = getattr(data, field, None)
            if value is not None:
                if field in ["seo_optimized", "is_public"]:
                    updates.append(f"{field} = ?")
                    params.append(1 if value else 0)
                else:
                    updates.append(f"{field} = ?")
                    params.append(value)
        
        if data.filter_tags is not None:
            updates.append("filter_tags = ?")
            params.append(json.dumps(data.filter_tags))
        
        if data.personality_tags is not None:
            updates.append("personality_tags = ?")
            params.append(json.dumps(data.personality_tags))
        
        if data.keywords is not None:
            updates.append("keywords = ?")
            params.append(json.dumps(data.keywords))
        
        if not updates:
            return existing
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        params.append(character_id)
        
        await db.execute(
            f"UPDATE characters SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        
        logger.info(f"Updated character: {character_id}")
        
        return await self.get_character_by_id(character_id)
    
    async def delete_character(self, character_id: str) -> bool:
        existing = await self.get_character_by_id(character_id)
        if not existing:
            return False
        
        await db.execute(
            "DELETE FROM characters WHERE id = ?",
            (character_id,)
        )
        
        logger.info(f"Deleted character: {character_id}")
        
        return True
    
    async def batch_delete(self, character_ids: list[str]) -> int:
        if not character_ids:
            return 0
        
        placeholders = ", ".join(["?" for _ in character_ids])
        result = await db.execute(
            f"DELETE FROM characters WHERE id IN ({placeholders})",
            tuple(character_ids)
        )
        
        logger.info(f"Batch deleted {len(character_ids)} characters")
        
        return len(character_ids)
    
    async def increment_chat_count(self, character_id: str) -> None:
        await db.execute(
            "UPDATE characters SET chat_count = chat_count + 1, updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), character_id)
        )
    
    async def increment_view_count(self, character_id: str) -> None:
        await db.execute(
            "UPDATE characters SET view_count = view_count + 1, updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), character_id)
        )
    
    async def update_popularity_score(self, character_id: str, score: float) -> None:
        await db.execute(
            "UPDATE characters SET popularity_score = ?, updated_at = ? WHERE id = ?",
            (score, datetime.utcnow().isoformat(), character_id)
        )
    
    async def get_categories_with_counts(self) -> list[dict]:
        rows = await db.execute(
            """
            SELECT top_category, COUNT(*) as count 
            FROM characters 
            WHERE is_official = 1 AND is_public = 1 
            GROUP BY top_category
            """,
            fetch_all=True
        )
        
        return [{"slug": row["top_category"], "count": row["count"]} for row in rows]
    
    async def get_filter_tags(self, top_category: str) -> list[dict]:
        rows = await db.execute(
            "SELECT filter_tags, personality_tags FROM characters WHERE top_category = ? AND is_official = 1 AND is_public = 1",
            (top_category,),
            fetch_all=True
        )
        
        tag_counts = {}
        
        for row in rows:
            for field in ["filter_tags", "personality_tags"]:
                if row[field]:
                    try:
                        tags = json.loads(row[field])
                        for tag in tags:
                            tag_counts[tag] = tag_counts.get(tag, 0) + 1
                    except (json.JSONDecodeError, TypeError):
                        pass
        
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return [{"slug": tag, "display_name": tag, "count": count} for tag, count in sorted_tags]
    
    async def list_pending_characters(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        count_row = await db.execute(
            "SELECT COUNT(*) as total FROM characters WHERE review_status = ?",
            ("pending",),
            fetch=True
        )
        total = count_row["total"] if count_row else 0
        
        offset = (page - 1) * page_size
        rows = await db.execute(
            "SELECT * FROM characters WHERE review_status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
            ("pending", page_size, offset),
            fetch_all=True
        )
        
        characters = [self._row_to_dict(row) for row in rows]
        
        return characters, total
    
    async def approve_character(self, character_id: str, reviewer_id: str) -> Optional[dict]:
        character = await self.get_character_by_id(character_id)
        if not character:
            return None
        
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """UPDATE characters SET 
               review_status = ?, 
               is_public = 1,
               reviewed_at = ?, 
               reviewer_id = ?, 
               rejection_reason = NULL,
               updated_at = ?
               WHERE id = ?""",
            ("approved", now, reviewer_id, now, character_id)
        )
        
        logger.info(f"Character approved: {character_id} by {reviewer_id}")
        
        return await self.get_character_by_id(character_id)
    
    async def reject_character(
        self, 
        character_id: str, 
        reviewer_id: str, 
        reason: Optional[str] = None
    ) -> Optional[dict]:
        character = await self.get_character_by_id(character_id)
        if not character:
            return None
        
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """UPDATE characters SET 
               review_status = ?, 
               is_public = 0,
               reviewed_at = ?, 
               reviewer_id = ?, 
               rejection_reason = ?,
               updated_at = ?
               WHERE id = ?""",
            ("rejected", now, reviewer_id, reason, now, character_id)
        )
        
        logger.info(f"Character rejected: {character_id} by {reviewer_id}, reason: {reason}")
        
        return await self.get_character_by_id(character_id)
    
    async def create_ugc_character(self, data: CharacterCreate, creator_id: str) -> dict:
        character_id = generate_character_id()
        slug = data.slug or generate_slug(data.name)
        
        existing = await self.get_character_by_slug(slug)
        if existing:
            slug = f"{slug}-{character_id[-6:]}"
        
        now = datetime.utcnow().isoformat()
        
        character_data = {
            "id": character_id,
            "name": data.name,
            "first_name": data.first_name,
            "slug": slug,
            "description": data.description,
            "age": data.age,
            "gender": data.gender or "female",
            "ethnicity": data.ethnicity,
            "nationality": data.nationality,
            "occupation": data.occupation,
            "top_category": data.top_category or "girls",
            "sub_category": data.sub_category,
            "filter_tags": json.dumps(data.filter_tags) if data.filter_tags else None,
            "personality_tags": json.dumps(data.personality_tags) if data.personality_tags else None,
            "keywords": json.dumps(data.keywords) if data.keywords else None,
            "personality_summary": data.personality_summary,
            "personality_example": data.personality_example,
            "backstory": data.backstory,
            "system_prompt": data.system_prompt,
            "greeting": data.greeting,
            "avatar_url": data.avatar_url,
            "cover_url": data.cover_url,
            "avatar_card_url": data.avatar_card_url,
            "profile_image_url": data.profile_image_url,
            "preview_video_url": data.preview_video_url,
            "voice_id": data.voice_id,
            "meta_title": data.meta_title,
            "meta_description": data.meta_description,
            "seo_optimized": 0,
            "is_official": 0,
            "is_public": 0,
            "template_id": data.template_id,
            "generation_mode": data.generation_mode or "ugc",
            "popularity_score": 0.0,
            "chat_count": 0,
            "view_count": 0,
            "creator_id": creator_id,
            "review_status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        
        columns = ", ".join(character_data.keys())
        placeholders = ", ".join(["?" for _ in character_data])
        values = list(character_data.values())
        
        await db.execute(
            f"INSERT INTO characters ({columns}) VALUES ({placeholders})",
            tuple(values)
        )
        
        logger.info(f"Created UGC character: {character_id} - {data.name} by user {creator_id}")
        
        return await self.get_character_by_id(character_id)
    
    async def list_user_characters(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        conditions = ["creator_id = ?"]
        params = [user_id]
        
        where_clause = " AND ".join(conditions)
        
        count_row = await db.execute(
            f"SELECT COUNT(*) as total FROM characters WHERE {where_clause}",
            tuple(params),
            fetch=True
        )
        total = count_row["total"] if count_row else 0
        
        offset = (page - 1) * page_size
        rows = await db.execute(
            f"SELECT * FROM characters WHERE {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?",
            tuple(params + [page_size, offset]),
            fetch_all=True
        )
        
        characters = [self._row_to_dict(row) for row in rows]
        
        return characters, total
    
    def _row_to_dict(self, row: dict) -> dict:
        result = dict(row)
        
        for field in ["filter_tags", "personality_tags", "keywords", "extra_data"]:
            if result.get(field) and isinstance(result[field], str):
                try:
                    result[field] = json.loads(result[field])
                except json.JSONDecodeError:
                    result[field] = []
            elif result.get(field) is None:
                result[field] = []
        
        for field in ["is_official", "is_public", "seo_optimized"]:
            if field in result and result[field] is not None:
                result[field] = bool(result[field])
        
        return result


character_service = CharacterService()
