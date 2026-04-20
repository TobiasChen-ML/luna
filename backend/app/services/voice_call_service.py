import logging
import json
from datetime import datetime, timedelta
from typing import Optional
import asyncio

from .redis_service import RedisService
from .database_service import DatabaseService
from .credit_service import CreditService, InsufficientCreditsError

logger = logging.getLogger(__name__)


class VoiceCallService:
    VOICE_CALL_PREFIX = "voice_call:"
    CALL_HISTORY_PREFIX = "voice_call_history:"
    
    def __init__(
        self,
        redis: Optional[RedisService] = None,
        db: Optional[DatabaseService] = None,
        credit_service: Optional[CreditService] = None,
    ):
        self.redis = redis or RedisService()
        self.db = db or DatabaseService()
        self.credit_service = credit_service or CreditService()
    
    async def start_call(
        self,
        room_name: str,
        user_id: str,
        character_id: str,
        session_id: Optional[str] = None,
    ) -> dict:
        call_data = {
            "room_name": room_name,
            "user_id": user_id,
            "character_id": character_id,
            "session_id": session_id,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "duration_seconds": 0,
            "credits_charged": 0,
            "status": "active",
        }
        
        await self.redis.set_json(
            f"{self.VOICE_CALL_PREFIX}{room_name}",
            call_data,
            ex=86400,
        )
        
        logger.info(f"Voice call started: room={room_name}, user={user_id}")
        return call_data
    
    async def get_call(self, room_name: str) -> Optional[dict]:
        return await self.redis.get_json(f"{self.VOICE_CALL_PREFIX}{room_name}")
    
    async def end_call(self, room_name: str) -> Optional[dict]:
        call_data = await self.get_call(room_name)
        if not call_data:
            logger.warning(f"Call not found for room: {room_name}")
            return None
        
        if call_data.get("status") == "ended":
            logger.info(f"Call already ended: room={room_name}")
            return call_data
        
        start_time = datetime.fromisoformat(call_data["start_time"])
        end_time = datetime.utcnow()
        duration_seconds = (end_time - start_time).total_seconds()
        
        credits_charged = await self._calculate_and_charge_credits(
            user_id=call_data["user_id"],
            duration_seconds=duration_seconds,
            character_id=call_data.get("character_id"),
            session_id=call_data.get("session_id"),
        )
        
        call_data["end_time"] = end_time.isoformat()
        call_data["duration_seconds"] = duration_seconds
        call_data["credits_charged"] = credits_charged
        call_data["status"] = "ended"
        
        await self.redis.set_json(
            f"{self.VOICE_CALL_PREFIX}{room_name}",
            call_data,
            ex=3600,
        )
        
        await self._save_call_history(call_data)
        
        logger.info(
            f"Voice call ended: room={room_name}, user={call_data['user_id']}, "
            f"duration={duration_seconds:.1f}s, credits={credits_charged}"
        )
        
        return call_data
    
    async def _calculate_and_charge_credits(
        self,
        user_id: str,
        duration_seconds: float,
        character_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> float:
        config = await self.credit_service.get_config()
        credits_per_minute = config.get("voice_call_per_minute", 3)
        
        duration_minutes = duration_seconds / 60.0
        credits_to_charge = credits_per_minute * duration_minutes
        
        credits_to_charge = round(credits_to_charge, 2)
        
        if credits_to_charge <= 0:
            return 0.0
        
        try:
            balance = await self.credit_service.get_balance(user_id)
            if balance.get("total", 0) >= credits_to_charge:
                await self.credit_service.deduct_credits(
                    user_id=user_id,
                    amount=credits_to_charge,
                    usage_type="voice_call",
                    character_id=character_id,
                    session_id=session_id,
                    description=f"Voice call: {duration_minutes:.1f} minutes",
                )
                return credits_to_charge
            else:
                logger.warning(
                    f"Insufficient credits for voice call billing: "
                    f"user={user_id}, needed={credits_to_charge}, has={balance.get('total', 0)}"
                )
                return 0.0
        except InsufficientCreditsError as e:
            logger.error(f"Failed to charge credits for voice call: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Unexpected error charging credits: {e}")
            return 0.0
    
    async def _save_call_history(self, call_data: dict) -> None:
        try:
            history_key = f"{self.CALL_HISTORY_PREFIX}{call_data['user_id']}"
            
            existing = await self.redis.get_json(history_key)
            if existing is None:
                existing = []
            elif isinstance(existing, dict):
                existing = []
            
            existing.append({
                "room_name": call_data["room_name"],
                "character_id": call_data.get("character_id"),
                "start_time": call_data["start_time"],
                "end_time": call_data["end_time"],
                "duration_seconds": call_data["duration_seconds"],
                "credits_charged": call_data["credits_charged"],
            })
            
            if len(existing) > 100:
                existing = existing[-100:]
            
            await self.redis.set_json(history_key, existing, ex=86400 * 30)
        except Exception as e:
            logger.error(f"Failed to save call history: {e}")
    
    async def get_active_call_duration(self, room_name: str) -> float:
        call_data = await self.get_call(room_name)
        if not call_data or call_data.get("status") != "active":
            return 0.0
        
        start_time = datetime.fromisoformat(call_data["start_time"])
        return (datetime.utcnow() - start_time).total_seconds()
    
    async def check_credits_for_call(
        self,
        user_id: str,
        estimated_minutes: float = 1.0,
    ) -> dict:
        config = await self.credit_service.get_config()
        credits_per_minute = config.get("voice_call_per_minute", 3)
        required_credits = credits_per_minute * estimated_minutes
        
        balance = await self.credit_service.get_balance(user_id)
        has_sufficient = balance.get("total", 0) >= required_credits
        
        return {
            "has_sufficient_credits": has_sufficient,
            "current_balance": balance.get("total", 0),
            "required_credits": required_credits,
            "credits_per_minute": credits_per_minute,
        }


voice_call_service = VoiceCallService()
