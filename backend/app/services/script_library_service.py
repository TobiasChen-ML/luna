"""
Script Library Service
Handles CRUD operations for script library
"""
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.core.database import db
from app.models.script_library import (
    ScriptLibrary,
    ScriptLibraryCreate,
    ScriptLibraryUpdate,
    ScriptLibraryListResponse,
    ScriptTag,
    ScriptTagsByCategory,
    ScriptLibraryStatus,
)

logger = logging.getLogger(__name__)


class ScriptLibraryService:
    _instance = None
    
    def __init__(self):
        pass
    
    @classmethod
    def get_instance(cls) -> "ScriptLibraryService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def list_scripts(
        self,
        emotion_tones: List[str] = None,
        relation_types: List[str] = None,
        contrast_types: List[str] = None,
        era: str = None,
        gender_target: str = None,
        character_gender: str = None,
        profession: str = None,
        age_rating: str = None,
        length: str = None,
        search: str = None,
        status: str = "published",
        page: int = 1,
        page_size: int = 20
    ) -> ScriptLibraryListResponse:
        query = "SELECT * FROM script_library WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if emotion_tones:
            for tone in emotion_tones:
                query += " AND emotion_tones LIKE ?"
                params.append(f'%"{tone}"%')
        
        if relation_types:
            for rel in relation_types:
                query += " AND relation_types LIKE ?"
                params.append(f'%"{rel}"%')
        
        if contrast_types:
            for ct in contrast_types:
                query += " AND contrast_types LIKE ?"
                params.append(f'%"{ct}"%')
        
        if era:
            query += " AND era = ?"
            params.append(era)
        
        if gender_target:
            query += " AND gender_target = ?"
            params.append(gender_target)
        
        if character_gender:
            query += " AND character_gender = ?"
            params.append(character_gender)
        
        if profession:
            query += " AND profession = ?"
            params.append(profession)
        
        if age_rating == "exclude_mature":
            query += " AND age_rating != ?"
            params.append("mature")
        elif age_rating:
            query += " AND age_rating = ?"
            params.append(age_rating)
        
        if length:
            query += " AND length = ?"
            params.append(length)
        
        if search:
            query += " AND (title LIKE ? OR summary LIKE ? OR title_en LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
        
        count_query = query.replace("SELECT *", "SELECT COUNT(*) as total")
        count_result = await db.execute(count_query, tuple(params), fetch=True)
        total = count_result.get("total", 0) if count_result else 0
        
        query += " ORDER BY popularity DESC, created_at DESC LIMIT ? OFFSET ?"
        params.extend([page_size, (page - 1) * page_size])
        
        rows = await db.execute(query, tuple(params), fetch_all=True)
        
        items = [self._row_to_model(r) for r in rows] if rows else []
        
        return ScriptLibraryListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )
    
    async def get_script(self, script_id: str) -> Optional[ScriptLibrary]:
        row = await db.execute(
            "SELECT * FROM script_library WHERE id = ?",
            (script_id,),
            fetch=True
        )
        return self._row_to_model(row) if row else None
    
    async def create_script(self, data: ScriptLibraryCreate) -> ScriptLibrary:
        script_id = f"script_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """INSERT INTO script_library 
               (id, title, title_en, summary, emotion_tones, relation_types,
                contrast_types, era, gender_target, character_gender, profession,
                length, age_rating, contrast_surface, contrast_truth, contrast_hook,
                script_seed, full_script, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                script_id,
                data.title,
                data.title_en,
                data.summary,
                json.dumps(data.emotion_tones),
                json.dumps(data.relation_types),
                json.dumps(data.contrast_types),
                data.era,
                data.gender_target,
                data.character_gender,
                data.profession,
                data.length,
                data.age_rating,
                data.contrast_surface,
                data.contrast_truth,
                data.contrast_hook,
                data.script_seed.model_dump_json() if data.script_seed else None,
                json.dumps(data.full_script) if data.full_script else None,
                ScriptLibraryStatus.DRAFT.value,
                now,
                now
            )
        )
        
        return await self.get_script(script_id)
    
    async def update_script(self, script_id: str, data: ScriptLibraryUpdate) -> Optional[ScriptLibrary]:
        existing = await self.get_script(script_id)
        if not existing:
            return None
        
        updates = ["updated_at = ?"]
        params = [datetime.utcnow().isoformat()]
        
        update_fields = [
            ("title", data.title),
            ("title_en", data.title_en),
            ("summary", data.summary),
            ("emotion_tones", json.dumps(data.emotion_tones) if data.emotion_tones is not None else None),
            ("relation_types", json.dumps(data.relation_types) if data.relation_types is not None else None),
            ("contrast_types", json.dumps(data.contrast_types) if data.contrast_types is not None else None),
            ("era", data.era),
            ("gender_target", data.gender_target),
            ("character_gender", data.character_gender),
            ("profession", data.profession),
            ("length", data.length),
            ("age_rating", data.age_rating),
            ("contrast_surface", data.contrast_surface),
            ("contrast_truth", data.contrast_truth),
            ("contrast_hook", data.contrast_hook),
            ("script_seed", data.script_seed.model_dump_json() if data.script_seed else None),
            ("full_script", json.dumps(data.full_script) if data.full_script else None),
            ("status", data.status.value if data.status else None),
        ]
        
        for field_name, value in update_fields:
            if value is not None:
                updates.append(f"{field_name} = ?")
                params.append(value)
        
        params.append(script_id)
        
        await db.execute(
            f"UPDATE script_library SET {', '.join(updates)} WHERE id = ?",
            tuple(params)
        )
        
        return await self.get_script(script_id)
    
    async def delete_script(self, script_id: str) -> bool:
        existing = await self.get_script(script_id)
        if not existing:
            return False
        
        await db.execute("DELETE FROM script_library WHERE id = ?", (script_id,))
        return True
    
    async def increment_popularity(self, script_id: str) -> None:
        await db.execute(
            "UPDATE script_library SET popularity = popularity + 1 WHERE id = ?",
            (script_id,)
        )
    
    async def get_all_tags(self) -> ScriptTagsByCategory:
        rows = await db.execute(
            "SELECT * FROM script_tags ORDER BY category, name",
            fetch_all=True
        )
        
        result = ScriptTagsByCategory()
        
        for row in (rows or []):
            category = row.get("category")
            tag = ScriptTag(
                id=row.get("id"),
                category=category,
                name=row.get("name"),
                name_en=row.get("name_en"),
                description=row.get("description"),
                examples=json.loads(row.get("examples") or "[]"),
                parent_id=row.get("parent_id")
            )
            
            if category == "emotion_tones":
                result.emotion_tones.append(tag)
            elif category == "relation_types":
                result.relation_types.append(tag)
            elif category == "contrast_types":
                result.contrast_types.append(tag)
            elif category == "eras":
                result.eras.append(tag)
            elif category == "professions":
                result.professions.append(tag)
            elif category == "gender_targets":
                result.gender_targets.append(tag)
            elif category == "character_genders":
                result.character_genders.append(tag)
            elif category == "lengths":
                result.lengths.append(tag)
            elif category == "age_ratings":
                result.age_ratings.append(tag)
        
        return result
    
    async def get_tags_by_category(self, category: str) -> List[ScriptTag]:
        rows = await db.execute(
            "SELECT * FROM script_tags WHERE category = ? ORDER BY name",
            (category,),
            fetch_all=True
        )
        
        return [
            ScriptTag(
                id=row.get("id"),
                category=row.get("category"),
                name=row.get("name"),
                name_en=row.get("name_en"),
                description=row.get("description"),
                examples=json.loads(row.get("examples") or "[]"),
                parent_id=row.get("parent_id")
            )
            for row in (rows or [])
        ]
    
    async def get_random_scripts(self, count: int = 5, status: str = "published") -> List[ScriptLibrary]:
        rows = await db.execute(
            "SELECT * FROM script_library WHERE status = ? ORDER BY RANDOM() LIMIT ?",
            (status, count),
            fetch_all=True
        )
        
        return [self._row_to_model(r) for r in rows] if rows else []
    
    def _row_to_model(self, row: dict) -> ScriptLibrary:
        if not row:
            return None
        
        script_seed = None
        seed_json = row.get("script_seed")
        if seed_json:
            try:
                seed_data = json.loads(seed_json)
                script_seed = seed_data
            except:
                pass
        
        return ScriptLibrary(
            id=row.get("id"),
            title=row.get("title"),
            title_en=row.get("title_en"),
            summary=row.get("summary"),
            emotion_tones=json.loads(row.get("emotion_tones") or "[]"),
            relation_types=json.loads(row.get("relation_types") or "[]"),
            contrast_types=json.loads(row.get("contrast_types") or "[]"),
            era=row.get("era"),
            gender_target=row.get("gender_target"),
            character_gender=row.get("character_gender"),
            profession=row.get("profession"),
            length=row.get("length"),
            age_rating=row.get("age_rating"),
            contrast_surface=row.get("contrast_surface"),
            contrast_truth=row.get("contrast_truth"),
            contrast_hook=row.get("contrast_hook"),
            script_seed=script_seed,
            full_script=json.loads(row.get("full_script") or "{}") if row.get("full_script") else None,
            popularity=row.get("popularity", 0),
            status=row.get("status", "draft"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at")
        )


script_library_service = ScriptLibraryService()
