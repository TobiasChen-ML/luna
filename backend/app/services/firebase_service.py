import logging
import os
from pathlib import Path
from typing import Optional
import firebase_admin
from firebase_admin import auth, credentials
from ..core.config import get_settings

# Backend package root: backend/app/services/ → backend/
_BACKEND_DIR = Path(__file__).resolve().parents[2]

logger = logging.getLogger(__name__)


class FirebaseService:
    _initialized = False
    
    def __init__(self):
        self.settings = get_settings()
        self._init_firebase()
    
    def _init_firebase(self):
        if FirebaseService._initialized:
            return

        # If the default app already exists (e.g. from a previous failed attempt),
        # mark as initialized rather than throwing "already exists".
        try:
            firebase_admin.get_app()
            FirebaseService._initialized = True
            logger.info("Firebase default app already exists — reusing")
            return
        except ValueError:
            pass  # No default app yet, proceed with initialization

        try:
            if self.settings.firebase_credentials_path:
                creds_path = Path(self.settings.firebase_credentials_path)
                if not creds_path.is_absolute():
                    creds_path = (_BACKEND_DIR / creds_path).resolve()
                if not creds_path.exists():
                    raise FileNotFoundError(f"Firebase credentials file not found: {creds_path}")
                cred = credentials.Certificate(str(creds_path))
                logger.info(f"Loading Firebase credentials from: {creds_path}")
            elif self.settings.firebase_project_id:
                cred = credentials.ApplicationDefault()
            else:
                logger.warning("No Firebase credentials configured")
                return

            firebase_admin.initialize_app(cred, {
                'projectId': self.settings.firebase_project_id
            })
            FirebaseService._initialized = True
            logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}", exc_info=True)
    
    def verify_token(self, token: str) -> Optional[dict]:
        try:
            decoded = auth.verify_id_token(token)
            return decoded
        except auth.ExpiredIdTokenError:
            logger.warning("Token expired")
            return None
        except auth.InvalidIdTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def create_custom_token(self, uid: str, claims: Optional[dict] = None) -> Optional[str]:
        try:
            token = auth.create_custom_token(uid, additional_claims=claims)
            return token.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to create custom token: {e}")
            return None
    
    def get_user_by_uid(self, uid: str) -> Optional[auth.UserRecord]:
        try:
            return auth.get_user(uid)
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
    
    def create_user(self, email: str, password: Optional[str] = None, uid: Optional[str] = None) -> Optional[auth.UserRecord]:
        try:
            properties = {'email': email}
            if password:
                properties['password'] = password
            if uid:
                properties['uid'] = uid
            
            return auth.create_user(**properties)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None
    
    def delete_user(self, uid: str) -> bool:
        try:
            auth.delete_user(uid)
            return True
        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False