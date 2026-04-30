import os
import logging
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional, Any
from functools import lru_cache

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


def resolve_sqlite_path(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        return database_url

    raw_path = database_url.replace("sqlite:///", "", 1)
    if raw_path == ":memory:":
        return raw_path

    db_path = Path(raw_path)
    if not db_path.is_absolute():
        base_dir = REPO_ROOT if db_path.parts and db_path.parts[0] == "backend" else BACKEND_DIR
        db_path = base_dir / db_path

    return str(db_path.resolve())


def normalize_database_url(database_url: str) -> str:
    if not database_url.startswith("sqlite:///"):
        return database_url

    db_path = resolve_sqlite_path(database_url)
    if db_path == ":memory:":
        return "sqlite:///:memory:"

    return f"sqlite:///{Path(db_path).as_posix()}"


class Settings(BaseSettings):
    app_name: str = "Roxy API"
    app_version: str = "0.1.0"
    debug: bool = False
    api_v1_prefix: str = "/v1"
    api_prefix: str = "/api"

    firebase_project_id: Optional[str] = None
    firebase_credentials_path: Optional[str] = None

    database_url: str = "sqlite:///./roxy.db"
    redis_url: str = "redis://localhost:6379/0"

    llm_provider: str = "novita"
    llm_api_key: Optional[str] = None
    llm_base_url: str = "https://api.novita.ai/openai/v1"
    llm_primary_model: str = "sao10k/l3-8b-lunaris"
    llm_fallback_model: str = "deepseek/deepseek-v3.2"
    llm_structured_model: str = "deepseek/deepseek-v3.2"
    llm_timeout: int = 120

    novita_api_key: Optional[str] = None
    novita_base_url: str = "https://api.novita.ai/v3"
    novita_webhook_base_url: Optional[str] = None

    elevenlabs_api_key: Optional[str] = None
    elevenlabs_base_url: str = "https://api.elevenlabs.io/v1"

    sora_api_key: Optional[str] = None
    sora_base_url: Optional[str] = None

    image_provider: str = "novita"
    image_txt2img_model: str = "juggernautXL_v9Rdphoto2Lightning_285361.safetensors"
    image_img2img_model: str = "juggernautXL_v9Rdphoto2Lightning_285361.safetensors"
    image_default_width: int = 1024
    image_default_height: int = 1024
    image_default_steps: int = 20
    image_default_cfg: float = 7.5
    img2img_strength: float = 0.7
    img2img_sampler: str = "DPM++ 2M"

    video_provider: str = "novita"
    video_model: str = "wan_i2v_22"

    r2_account_id: Optional[str] = None
    r2_access_key_id: Optional[str] = None
    r2_secret_access_key: Optional[str] = None
    r2_bucket_name: str = "roxy-media"
    r2_endpoint_url: Optional[str] = None

    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    ccbill_client_id: Optional[str] = None
    ccbill_client_secret: Optional[str] = None
    crypto_payment_address_usdc_polygon: Optional[str] = None
    crypto_payment_address_usdt_polygon: Optional[str] = None
    crypto_payment_address_usdc_bep20: Optional[str] = None
    crypto_payment_address_usdt_bep20: Optional[str] = None
    crypto_payment_address_usdt_trc20: Optional[str] = None
    crypto_payment_address_pool_usdc_polygon: Optional[str] = None
    crypto_payment_address_pool_usdt_polygon: Optional[str] = None
    crypto_payment_address_pool_usdc_bep20: Optional[str] = None
    crypto_payment_address_pool_usdt_bep20: Optional[str] = None
    crypto_payment_address_pool_usdt_trc20: Optional[str] = None

    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from_email: Optional[str] = None

    recaptcha_secret_key: Optional[str] = None

    livekit_api_key: Optional[str] = None
    livekit_api_secret: Optional[str] = None
    livekit_ws_url: Optional[str] = None

    telegram_bot_token: Optional[str] = None
    telegram_admin_user_id: Optional[str] = None
    telegram_bot_username: Optional[str] = None
    telegram_bot_webhook_secret: Optional[str] = None

    admin_password: Optional[str] = None
    admin_emails: list[str] = ["admin@roxy.ai"]

    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    memory_decay_rate: float = 0.05
    memory_decay_threshold: float = 1.0
    memory_importance_min: int = 1
    memory_importance_max: int = 10

    embedding_provider: str = "local"
    embedding_model: str = "all-MiniLM-L6-v2"
    chroma_persist_dir: str = "./chroma_db"
    vector_search_enabled: bool = True

    local_inference_enabled: bool = False
    local_model_url: str = "http://localhost:11434"
    local_model_name: str = "qwen2.5:1.5b"
    intent_routing_enabled: bool = True
    intent_confidence_threshold: float = 0.8

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    
    environment: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"
    
    def validate_security_settings(self) -> list[str]:
        warnings = []
        
        if self.environment == "production":
            if not self.jwt_secret or len(self.jwt_secret) < 32:
                raise ValueError("JWT_SECRET must be set and at least 32 characters in production")
            if not self.admin_password or len(self.admin_password) < 12:
                raise ValueError("ADMIN_PASSWORD must be set and at least 12 characters in production")
            if "*" in self.cors_origins:
                raise ValueError("Cannot use wildcard CORS origin (*) in production")
        else:
            if not self.jwt_secret:
                warnings.append("JWT_SECRET not set - using insecure default for development")
            if not self.admin_password:
                warnings.append("ADMIN_PASSWORD not set - admin login disabled")
        
        return warnings
    
    def get_jwt_secret(self) -> str:
        if not self.jwt_secret:
            if self.environment == "production":
                raise ValueError("JWT_SECRET must be configured in production")
            import secrets
            dev_secret = secrets.token_urlsafe(32)
            logger.warning(
                "JWT_SECRET not set - using generated secret for development. "
                "Tokens will be invalidated on server restart."
            )
            return dev_secret
        return self.jwt_secret
    
    def get_admin_password(self) -> Optional[str]:
        return self.admin_password


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


ENV_TO_SETTINGS_MAP = {
    "LLM_PROVIDER": "llm_provider",
    "LLM_API_KEY": "llm_api_key",
    "LLM_BASE_URL": "llm_base_url",
    "LLM_CHAT_MODEL": "llm_primary_model",
    "LLM_ORCHESTRATOR_MODEL": "llm_fallback_model",
    "LLM_INTENT_MODEL": "llm_structured_model",
    "LLM_LOCAL_BASE_URL": "local_model_url",
    "NOVITA_API_KEY": "novita_api_key",
    "NOVITA_BASE_URL": "novita_base_url",
    "NOVITA_WEBHOOK_BASE_URL": "novita_webhook_base_url",
    "ELEVENLABS_API_KEY": "elevenlabs_api_key",
    "R2_ACCESS_KEY_ID": "r2_access_key_id",
    "R2_SECRET_ACCESS_KEY": "r2_secret_access_key",
    "R2_BUCKET_NAME": "r2_bucket_name",
    "R2_ENDPOINT_URL": "r2_endpoint_url",
    "STRIPE_SECRET_KEY": "stripe_secret_key",
    "STRIPE_WEBHOOK_SECRET": "stripe_webhook_secret",
    "LIVEKIT_API_KEY": "livekit_api_key",
    "LIVEKIT_API_SECRET": "livekit_api_secret",
    "LIVEKIT_WS_URL": "livekit_ws_url",
    "TELEGRAM_BOT_TOKEN": "telegram_bot_token",
    "TELEGRAM_BOT_WEBHOOK_SECRET": "telegram_bot_webhook_secret",
    "ELEVENLABS_BASE_URL": "elevenlabs_base_url",
    "SORA_API_KEY": "sora_api_key",
    "SORA_BASE_URL": "sora_base_url",
    "IMAGE_PROVIDER": "image_provider",
    "IMAGE_TXT2IMG_MODEL": "image_txt2img_model",
    "IMAGE_IMG2IMG_MODEL": "image_img2img_model",
    "IMAGE_DEFAULT_WIDTH": "image_default_width",
    "IMAGE_DEFAULT_HEIGHT": "image_default_height",
    "IMAGE_DEFAULT_STEPS": "image_default_steps",
    "IMAGE_DEFAULT_CFG": "image_default_cfg",
    "IMG2IMG_STRENGTH": "img2img_strength",
    "IMG2IMG_SAMPLER": "img2img_sampler",
    "VIDEO_PROVIDER": "video_provider",
    "VIDEO_MODEL": "video_model",
    "SMTP_ADDRESS": "smtp_host",
    "SMTP_PORT": "smtp_port",
    "SMTP_USERNAME": "smtp_user",
    "SMTP_PASSWORD": "smtp_password",
    "SMTP_FROM_EMAIL": "smtp_from_email",
    "RECAPTCHA_SECRET_KEY": "recaptcha_secret_key",
    "FIREBASE_PROJECT_ID": "firebase_project_id",
    "FIREBASE_CREDENTIALS_PATH": "firebase_credentials_path",
    "ADMIN_PASSWORD": "admin_password",
    "JWT_SECRET_KEY": "jwt_secret",
    "CORS_ORIGINS": "cors_origins",
    "RATE_LIMIT_PER_MINUTE": "rate_limit_per_minute",
    "RATE_LIMIT_PER_HOUR": "rate_limit_per_hour",
    "ENVIRONMENT": "environment",
    "EMBEDDING_PROVIDER": "embedding_provider",
    "EMBEDDING_MODEL": "embedding_model",
    "CHROMA_PERSIST_DIR": "chroma_persist_dir",
    "VECTOR_SEARCH_ENABLED": "vector_search_enabled",
    "LOCAL_INFERENCE_ENABLED": "local_inference_enabled",
    "LOCAL_MODEL_URL": "local_model_url",
    "LOCAL_MODEL_NAME": "local_model_name",
    "INTENT_ROUTING_ENABLED": "intent_routing_enabled",
    "INTENT_CONFIDENCE_THRESHOLD": "intent_confidence_threshold",
    "R2_PUBLIC_URL": "r2_public_url",
    "CCBILL_CLIENT_ID": "ccbill_client_id",
    "CCBILL_CLIENT_SECRET": "ccbill_client_secret",
    "USDT_WEBHOOK_SECRET": "usdt_webhook_secret",
    "CRYPTO_PAYMENT_GATEWAY_WEBHOOK_SECRET": "usdt_webhook_secret",
    "CRYPTO_PAYMENT_ADDRESS_USDC_POLYGON": "crypto_payment_address_usdc_polygon",
    "CRYPTO_PAYMENT_ADDRESS_USDT_POLYGON": "crypto_payment_address_usdt_polygon",
    "CRYPTO_PAYMENT_ADDRESS_USDC_BEP20": "crypto_payment_address_usdc_bep20",
    "CRYPTO_PAYMENT_ADDRESS_USDT_BEP20": "crypto_payment_address_usdt_bep20",
    "CRYPTO_PAYMENT_ADDRESS_USDT_TRC20": "crypto_payment_address_usdt_trc20",
    "CRYPTO_PAYMENT_ADDRESS_POOL_USDC_POLYGON": "crypto_payment_address_pool_usdc_polygon",
    "CRYPTO_PAYMENT_ADDRESS_POOL_USDT_POLYGON": "crypto_payment_address_pool_usdt_polygon",
    "CRYPTO_PAYMENT_ADDRESS_POOL_USDC_BEP20": "crypto_payment_address_pool_usdc_bep20",
    "CRYPTO_PAYMENT_ADDRESS_POOL_USDT_BEP20": "crypto_payment_address_pool_usdt_bep20",
    "CRYPTO_PAYMENT_ADDRESS_POOL_USDT_TRC20": "crypto_payment_address_pool_usdt_trc20",
    "LLM_TIMEOUT_SECONDS": "llm_timeout",
}

_config_cache: dict[str, Any] = {}


async def get_config_value(key: str, default: Optional[str] = None) -> Optional[str]:
    from app.services.config_service import ConfigService

    config_service = ConfigService()
    db_value = await config_service.get_config_value(key)
    if db_value is not None:
        _config_cache[key] = db_value
        return db_value

    if key in _config_cache:
        return _config_cache[key]

    env_value = os.environ.get(key)
    if env_value:
        _config_cache[key] = env_value
        return env_value

    if key in ENV_TO_SETTINGS_MAP:
        settings_attr = ENV_TO_SETTINGS_MAP[key]
        settings_value = getattr(settings, settings_attr, None)
        if settings_value is not None:
            _config_cache[key] = str(settings_value)
            return str(settings_value)

    if default is not None:
        return default

    return None


def get_config_value_sync(key: str, default: Optional[str] = None) -> Optional[str]:
    env_value = os.environ.get(key)
    if env_value:
        return env_value

    if key in ENV_TO_SETTINGS_MAP:
        settings_attr = ENV_TO_SETTINGS_MAP[key]
        settings_value = getattr(settings, settings_attr, None)
        if settings_value is not None:
            return str(settings_value)

    return default


def clear_config_cache() -> None:
    global _config_cache
    _config_cache = {}


async def get_llm_config() -> dict[str, Any]:
    return {
        "provider": await get_config_value("LLM_PROVIDER", "novita"),
        "api_key": await get_config_value("LLM_API_KEY"),
        "base_url": await get_config_value("LLM_BASE_URL"),
        "chat_model": await get_config_value("LLM_CHAT_MODEL"),
        "orchestrator_model": await get_config_value("LLM_ORCHESTRATOR_MODEL"),
        "intent_model": await get_config_value("LLM_INTENT_MODEL"),
        "timeout": int(await get_config_value("LLM_TIMEOUT_SECONDS", "300") or "300"),
    }


async def get_embedding_config() -> dict[str, Any]:
    return {
        "provider": await get_config_value("EMBEDDING_PROVIDER", "local"),
        "model": await get_config_value("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        "openai_api_key": await get_config_value("OPENAI_API_KEY"),
        "cf_account_id": await get_config_value("CF_ACCOUNT_ID"),
        "cf_api_token": await get_config_value("CF_API_TOKEN"),
        "chroma_persist_dir": await get_config_value("CHROMA_PERSIST_DIR", "./chroma_db"),
        "vector_search_enabled": (await get_config_value("VECTOR_SEARCH_ENABLED", "true") or "true").lower() == "true",
    }


async def get_storage_config() -> dict[str, Any]:
    return {
        "r2_access_key_id": await get_config_value("R2_ACCESS_KEY_ID"),
        "r2_secret_access_key": await get_config_value("R2_SECRET_ACCESS_KEY"),
        "r2_bucket_name": await get_config_value("R2_BUCKET_NAME", "aigirl-media"),
        "r2_endpoint_url": await get_config_value("R2_ENDPOINT_URL"),
        "r2_public_url": await get_config_value("R2_PUBLIC_URL"),
        "replicate_api_token": await get_config_value("REPLICATE_API_TOKEN"),
    }


async def get_payment_config() -> dict[str, Any]:
    telegram_stars_enabled = (
        await get_config_value("TELEGRAM_STARS_ENABLED")
        or await get_config_value("TELEGRAM_STAR_GATEWAY_ENABLED", "false")
        or "false"
    )
    crypto_gateway_enabled = (
        await get_config_value("CRYPTO_PAYMENT_GATEWAY_ENABLED")
        or await get_config_value("USDT_PAYMENT_GATEWAY_ENABLED", "false")
        or "false"
    )
    async def has_crypto_address(asset: str, network: str) -> bool:
        suffix = f"{asset}_{network}"
        return bool(
            await get_config_value(f"CRYPTO_PAYMENT_ADDRESS_POOL_{suffix}")
            or await get_config_value(f"CRYPTO_PAYMENT_ADDRESS_{suffix}")
            or await get_config_value(f"CRYPTO_PAYMENT_FALLBACK_ADDRESS_{suffix}")
        )

    return {
        "ccbill_enabled": (await get_config_value("CCBILL_ENABLED", "false") or "false").lower() == "true",
        "ccbill_merchant_id": await get_config_value("CCBILL_MERCHANT_ID"),
        "ccbill_subaccount": await get_config_value("CCBILL_SUBACCOUNT", "0000"),
        "ccbill_flexform_id": await get_config_value("CCBILL_FLEXFORM_ID"),
        "ccbill_salt": await get_config_value("CCBILL_SALT"),
        "crypto_gateway_enabled": crypto_gateway_enabled.lower() == "true",
        "crypto_gateway_base_url": (
            await get_config_value("CRYPTO_PAYMENT_GATEWAY_BASE_URL")
            or await get_config_value("USDT_PAYMENT_GATEWAY_BASE_URL")
        ),
        "crypto_gateway_api_key": (
            await get_config_value("CRYPTO_PAYMENT_GATEWAY_API_KEY")
            or await get_config_value("USDT_PAYMENT_GATEWAY_API_KEY")
        ),
        "crypto_gateway_create_path": await get_config_value("CRYPTO_PAYMENT_GATEWAY_CREATE_PATH", "/orders"),
        "crypto_gateway_webhook_secret_configured": bool(
            await get_config_value("CRYPTO_PAYMENT_GATEWAY_WEBHOOK_SECRET")
            or await get_config_value("USDT_WEBHOOK_SECRET")
        ),
        "crypto_local_addresses_configured": {
            "USDT_POLYGON": await has_crypto_address("USDT", "POLYGON"),
            "USDC_POLYGON": await has_crypto_address("USDC", "POLYGON"),
        },
        "usdt_gateway_enabled": crypto_gateway_enabled.lower() == "true",
        "usdt_gateway_base_url": (
            await get_config_value("CRYPTO_PAYMENT_GATEWAY_BASE_URL")
            or await get_config_value("USDT_PAYMENT_GATEWAY_BASE_URL")
        ),
        "usdt_gateway_api_key": (
            await get_config_value("CRYPTO_PAYMENT_GATEWAY_API_KEY")
            or await get_config_value("USDT_PAYMENT_GATEWAY_API_KEY")
        ),
        "telegram_stars_enabled": telegram_stars_enabled.lower() == "true",
        "telegram_bot_token_configured": bool(await get_config_value("TELEGRAM_BOT_TOKEN")),
        "telegram_webhook_secret_configured": bool(
            await get_config_value("TELEGRAM_WEBHOOK_SECRET_TOKEN")
            or await get_config_value("TELEGRAM_STAR_GATEWAY_WEBHOOK_AUTH_TOKEN")
            or await get_config_value("TELEGRAM_BOT_WEBHOOK_SECRET")
        ),
        "telegram_stars_base_url": (
            await get_config_value("TELEGRAM_STARS_BASE_URL")
            or await get_config_value("TELEGRAM_STAR_GATEWAY_BASE_URL")
        ),
        "telegram_stars_api_token": (
            await get_config_value("TELEGRAM_STARS_API_TOKEN")
            or await get_config_value("TELEGRAM_STAR_GATEWAY_API_TOKEN")
        ),
    }


async def get_smtp_config() -> dict[str, Any]:
    return {
        "host": await get_config_value("SMTP_ADDRESS"),
        "ssl_port": int(await get_config_value("SMTP_SSL_PORT", "465") or "465"),
        "starttls_port": int(await get_config_value("SMTP_STARTTLS_PORT", "587") or "587"),
        "use_ssl": (await get_config_value("SMTP_USE_SSL", "true") or "true").lower() == "true",
        "use_starttls": (await get_config_value("SMTP_USE_STARTTLS", "false") or "false").lower() == "true",
        "username": await get_config_value("SMTP_USERNAME"),
        "password": await get_config_value("SMTP_PASSWORD"),
        "from_email": await get_config_value("SMTP_FROM_EMAIL"),
        "from_name": await get_config_value("SMTP_FROM_NAME", "AIGirl Admin"),
    }


async def get_recaptcha_config() -> dict[str, Any]:
    return {
        "enabled": (await get_config_value("RECAPTCHA_ENABLED", "true") or "true").lower() == "true",
        "secret_key": await get_config_value("RECAPTCHA_SECRET_KEY"),
        "site_key": await get_config_value("RECAPTCHA_SITE_KEY"),
        "version": await get_config_value("RECAPTCHA_VERSION", "v3"),
        "min_score": float(await get_config_value("RECAPTCHA_MIN_SCORE", "0.5") or "0.5"),
    }


async def get_voice_config() -> dict[str, Any]:
    return {
        "enabled": (await get_config_value("ENABLE_VOICE_RESPONSE", "false") or "false").lower() == "true",
    }
