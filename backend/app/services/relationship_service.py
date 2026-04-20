import logging
import json
from typing import Optional
from datetime import datetime

from app.core.database import db
from app.models.relationship import (
    RelationshipCreate,
    RelationshipUpdate,
    RelationshipStage,
)

logger = logging.getLogger(__name__)

STAGE_THRESHOLDS = {
    "stranger": {"intimacy": 0, "trust": 0},
    "acquaintance": {"intimacy": 5, "trust": 5},
    "friend": {"intimacy": 20, "trust": 20},
    "close": {"intimacy": 40, "trust": 30},
    "intimate": {"intimacy": 60, "trust": 50},
    "soulmate": {"intimacy": 80, "trust": 70},
}

NEXT_STAGE_REQUIREMENTS = {
    "stranger": {"intimacy": 5, "trust": 5},
    "acquaintance": {"intimacy": 20, "trust": 20},
    "friend": {"intimacy": 40, "trust": 30},
    "close": {"intimacy": 60, "trust": 50},
    "intimate": {"intimacy": 80, "trust": 70},
    "soulmate": None,
}


class RelationshipService:
    _instance = None
    
    def __init__(self):
        pass
    
    @classmethod
    def get_instance(cls) -> "RelationshipService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def get_relationship(self, user_id: str, character_id: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM relationships WHERE user_id = ? AND character_id = ?",
            (user_id, character_id),
            fetch=True
        )
        return self._row_to_dict(row) if row else None
    
    async def get_or_create_relationship(
        self,
        user_id: str,
        character_id: str,
        script_id: Optional[str] = None,
    ) -> dict:
        existing = await self.get_relationship(user_id, character_id)
        if existing:
            return existing
        
        return await self.create_relationship(RelationshipCreate(
            user_id=user_id,
            character_id=character_id,
            script_id=script_id,
        ))
    
    async def create_relationship(self, data: RelationshipCreate) -> dict:
        import uuid
        rel_id = f"rel_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """INSERT INTO relationships
               (id, user_id, character_id, script_id, intimacy, trust, desire, dependency, stage, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                rel_id,
                data.user_id,
                data.character_id,
                data.script_id,
                data.intimacy,
                data.trust,
                data.desire,
                data.dependency,
                data.stage.value if isinstance(data.stage, RelationshipStage) else data.stage,
                now,
                now,
            )
        )
        
        logger.info(f"Created relationship: {rel_id} for user {data.user_id} and character {data.character_id}")
        return await self.get_relationship(data.user_id, data.character_id)
    
    async def update_relationship(
        self,
        user_id: str,
        character_id: str,
        data: RelationshipUpdate,
    ) -> Optional[dict]:
        existing = await self.get_relationship(user_id, character_id)
        if not existing:
            return None
        
        if existing.get("is_locked"):
            logger.warning(f"Relationship {user_id}/{character_id} is locked, cannot update")
            return existing
        
        updates = []
        params = []
        
        if data.intimacy is not None:
            updates.append("intimacy = ?")
            params.append(max(0, min(100, data.intimacy)))
        if data.trust is not None:
            updates.append("trust = ?")
            params.append(max(0, min(100, data.trust)))
        if data.desire is not None:
            updates.append("desire = ?")
            params.append(max(0, min(100, data.desire)))
        if data.dependency is not None:
            updates.append("dependency = ?")
            params.append(max(0, min(100, data.dependency)))
        if data.stage is not None:
            updates.append("stage = ?")
            params.append(data.stage.value if isinstance(data.stage, RelationshipStage) else data.stage)
        if data.history_summary is not None:
            updates.append("history_summary = ?")
            params.append(data.history_summary)
        if data.is_locked is not None:
            updates.append("is_locked = ?")
            updates.append("locked_at = ?")
            params.append(1 if data.is_locked else 0)
            params.append(datetime.utcnow().isoformat() if data.is_locked else None)
        
        if not updates:
            return existing
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        params.extend([user_id, character_id])
        
        await db.execute(
            f"UPDATE relationships SET {', '.join(updates)} WHERE user_id = ? AND character_id = ?",
            tuple(params)
        )
        
        logger.info(f"Updated relationship: {user_id}/{character_id}")
        return await self.get_relationship(user_id, character_id)
    
    async def update_attributes(
        self,
        user_id: str,
        character_id: str,
        intimacy_change: float = 0,
        trust_change: float = 0,
        desire_change: float = 0,
        dependency_change: float = 0,
    ) -> Optional[dict]:
        existing = await self.get_relationship(user_id, character_id)
        if not existing:
            return None
        
        new_intimacy = max(0, min(100, existing.get("intimacy", 0) + intimacy_change))
        new_trust = max(0, min(100, existing.get("trust", 0) + trust_change))
        new_desire = max(0, min(100, existing.get("desire", 0) + desire_change))
        new_dependency = max(0, min(100, existing.get("dependency", 0) + dependency_change))
        
        new_stage = self._determine_stage(new_intimacy, new_trust)
        
        return await self.update_relationship(
            user_id,
            character_id,
            RelationshipUpdate(
                intimacy=new_intimacy,
                trust=new_trust,
                desire=new_desire,
                dependency=new_dependency,
                stage=new_stage,
            )
        )
    
    def _determine_stage(self, intimacy: float, trust: float) -> RelationshipStage:
        stages = [
            ("soulmate", 80, 70),
            ("intimate", 60, 50),
            ("close", 40, 30),
            ("friend", 20, 20),
            ("acquaintance", 5, 5),
        ]
        
        for stage_name, req_i, req_t in stages:
            if intimacy >= req_i and trust >= req_t:
                return RelationshipStage(stage_name)
        
        return RelationshipStage.STRANGER
    
    def get_next_stage_requirements(self, current_stage: str) -> Optional[dict]:
        return NEXT_STAGE_REQUIREMENTS.get(current_stage)
    
    async def lock_relationship(self, user_id: str, character_id: str) -> Optional[dict]:
        return await self.update_relationship(
            user_id,
            character_id,
            RelationshipUpdate(is_locked=True)
        )
    
    async def unlock_relationship(self, user_id: str, character_id: str) -> Optional[dict]:
        return await self.update_relationship(
            user_id,
            character_id,
            RelationshipUpdate(is_locked=False)
        )
    
    def _row_to_dict(self, row: dict) -> dict:
        result = dict(row)
        if "is_locked" in result:
            result["is_locked"] = bool(result["is_locked"])
        return result


relationship_service = RelationshipService()
