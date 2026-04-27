import jwt
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class JWTService:
    def __init__(self):
        self.settings = get_settings()
    
    def create_access_token(
        self, 
        user_id: str, 
        email: str, 
        is_admin: bool = False,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.settings.jwt_expire_minutes
            )
        
        payload = {
            "sub": user_id,
            "email": email,
            "is_admin": is_admin,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        
        return jwt.encode(
            payload, 
            self.settings.get_jwt_secret(), 
            algorithm=self.settings.jwt_algorithm
        )
    
    def verify_token(self, token: str) -> Optional[dict]:
        try:
            payload = jwt.decode(
                token, 
                self.settings.get_jwt_secret(), 
                algorithms=[self.settings.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def create_refresh_token(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(days=30)
        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(
            payload, 
            self.settings.get_jwt_secret(), 
            algorithm=self.settings.jwt_algorithm
        )


class WebhookSignatureService:
    def __init__(self):
        self.settings = get_settings()
    
    def verify_stripe_signature(
        self, 
        payload: bytes, 
        signature: str, 
        secret: Optional[str] = None
    ) -> bool:
        secret = secret or self.settings.stripe_webhook_secret
        if not secret:
            logger.error("Stripe webhook secret not configured - rejecting all webhooks")
            return False
        
        try:
            import stripe
            stripe.Webhook.construct_event(payload, signature, secret)
            return True
        except ValueError:
            logger.warning("Invalid Stripe payload")
            return False
        except stripe.error.SignatureVerificationError:
            logger.warning("Invalid Stripe signature")
            return False
        except Exception as e:
            logger.error(f"Stripe webhook verification error: {e}")
            return False
    
    def verify_ccbill_signature(
        self,
        payload: dict,
        signature: str,
        client_secret: Optional[str] = None
    ) -> bool:
        client_secret = client_secret or self.settings.ccbill_client_secret
        if not client_secret:
            logger.error("CCBill client secret not configured - rejecting all webhooks")
            return False
        
        try:
            expected_sig = hmac.new(
                client_secret.encode(),
                json.dumps(payload, separators=(',', ':')).encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_sig)
        except Exception as e:
            logger.error(f"CCBill webhook verification error: {e}")
            return False
    
    def verify_usdt_signature(
        self,
        payload: dict,
        signature: str,
        secret: str
    ) -> bool:
        if not secret:
            logger.error("USDT webhook secret not configured - rejecting all webhooks")
            return False
        
        try:
            expected_sig = hmac.new(
                secret.encode(),
                json.dumps(payload, separators=(',', ':')).encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_sig)
        except Exception as e:
            logger.error(f"USDT webhook verification error: {e}")
            return False
    
    def verify_telegram_signature(
        self,
        payload: dict,
        bot_token: str
    ) -> bool:
        if not bot_token:
            logger.error("Telegram bot token not configured - rejecting all webhooks")
            return False
        
        try:
            received_hash = payload.get("hash", "")
            sorted_items = sorted(
                (key, value)
                for key, value in payload.items()
                if key != "hash" and value is not None
            )
            data_check_string = '\n'.join(f'{k}={v}' for k, v in sorted_items)
            
            secret_key = hashlib.sha256(bot_token.encode()).digest()
            expected_hash = hmac.new(
                secret_key,
                data_check_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(received_hash, expected_hash)
        except Exception as e:
            logger.error(f"Telegram signature verification error: {e}")
            return False


jwt_service = JWTService()
webhook_service = WebhookSignatureService()
