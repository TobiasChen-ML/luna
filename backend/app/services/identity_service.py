import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional
import hashlib

from ..core.config import get_settings
from .firebase_service import FirebaseService
from .email_service import EmailService
from .redis_service import RedisService
from .database_service import DatabaseService

logger = logging.getLogger(__name__)


class IdentityService:
    def __init__(
        self,
        firebase: Optional[FirebaseService] = None,
        email: Optional[EmailService] = None,
        redis: Optional[RedisService] = None,
        db: Optional[DatabaseService] = None,
    ):
        self.settings = get_settings()
        self.firebase = firebase or FirebaseService()
        self.email = email or EmailService()
        self.redis = redis or RedisService()
        self.db = db or DatabaseService()

    async def initiate_registration(self, email: str, recaptcha_token: Optional[str] = None) -> dict:
        verification_code = secrets.randbelow(900000) + 100000
        
        await self.redis.set(
            f"registration:{email}",
            {"code": str(verification_code), "created_at": datetime.utcnow().isoformat()},
            ex=3600,
        )
        
        await self.email.send_verification_email(email, verification_code)
        
        return {"message": "Verification email sent", "email": email}

    async def verify_email(self, email: str, code: str) -> dict:
        cached = await self.redis.get(f"registration:{email}")
        
        if not cached:
            raise ValueError("Verification code expired or not found")
        
        if str(cached.get("code")) != str(code):
            raise ValueError("Invalid verification code")
        
        await self.redis.set(
            f"registration:verified:{email}",
            {"verified": True, "verified_at": datetime.utcnow().isoformat()},
            ex=86400,
        )
        
        return {"message": "Email verified", "email": email}

    async def resend_verification(self, email: str) -> dict:
        cached = await self.redis.get(f"registration:verified:{email}")
        if cached and cached.get("verified"):
            raise ValueError("Email already verified")
        
        return await self.initiate_registration(email)

    async def complete_registration(
        self,
        email: str,
        display_name: str,
        password: str,
    ) -> dict:
        verified = await self.redis.get(f"registration:verified:{email}")
        if not verified or not verified.get("verified"):
            raise ValueError("Email not verified")
        
        user = self.firebase.create_user(email, password)
        if not user:
            raise ValueError("Failed to create user")
        
        with self.db.get_session() as session:
            from ..models.user import User
            db_user = User(
                firebase_uid=user.uid,
                email=email,
                display_name=display_name,
                subscription_tier="free",
                credits=0,
                is_verified=True,
            )
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            
            await self.redis.delete(f"registration:{email}")
            await self.redis.delete(f"registration:verified:{email}")
            
            return {
                "user_id": user.uid,
                "email": email,
                "display_name": display_name,
            }

    async def get_user_profile(self, firebase_uid: str) -> Optional[dict]:
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.firebase_uid == firebase_uid).first()
            
            if not user:
                return None
            
            return {
                "id": user.id,
                "firebase_uid": user.firebase_uid,
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "subscription_tier": user.subscription_tier,
                "credits": user.credits,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat(),
            }

    async def update_user_profile(
        self,
        firebase_uid: str,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[dict] = None,
    ) -> Optional[dict]:
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.firebase_uid == firebase_uid).first()
            
            if not user:
                return None
            
            if display_name:
                user.display_name = display_name
            if avatar_url:
                user.avatar_url = avatar_url
            if preferences:
                user.content_preferences = str(preferences)
            
            user.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(user)
            
            return await self.get_user_profile(firebase_uid)

    async def update_user_preferences(
        self,
        firebase_uid: str,
        preferences: dict,
    ) -> Optional[dict]:
        with self.db.get_session() as session:
            from ..models.user import User
            user = session.query(User).filter(User.firebase_uid == firebase_uid).first()
            
            if not user:
                return None
            
            user.voice_presence = preferences.get("voice_presence", "auto")
            user.content_preferences = str(preferences.get("content_preferences", {}))
            user.updated_at = datetime.utcnow()
            session.commit()
            
            return {"message": "Preferences updated"}

    async def start_age_verification(
        self,
        user_id: str,
        provider: str = "default",
    ) -> dict:
        verification_id = secrets.token_urlsafe(32)
        
        await self.redis.set(
            f"age_verification:{verification_id}",
            {
                "user_id": user_id,
                "provider": provider,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
            },
            ex=86400 * 7,
        )
        
        return {
            "verification_id": verification_id,
            "status": "pending",
        }

    async def get_age_verification_status(self, verification_id: str) -> Optional[dict]:
        return await self.redis.get(f"age_verification:{verification_id}")

    async def handle_age_verification_webhook(
        self,
        verification_id: str,
        payload: dict,
    ) -> dict:
        cached = await self.redis.get(f"age_verification:{verification_id}")
        
        if not cached:
            raise ValueError("Verification not found")
        
        status = payload.get("status", "pending")
        
        if status == "verified":
            user_id = cached.get("user_id")
            with self.db.get_session() as session:
                from ..models.user import User
                user = session.query(User).filter(User.firebase_uid == user_id).first()
                if user:
                    user.metadata = str({"age_verified": True, "verified_at": datetime.utcnow().isoformat()})
                    session.commit()
        
        await self.redis.set(
            f"age_verification:{verification_id}",
            {
                **cached,
                "status": status,
                "result": payload,
                "updated_at": datetime.utcnow().isoformat(),
            },
            ex=86400 * 30,
        )
        
        return {"verification_id": verification_id, "status": status}
