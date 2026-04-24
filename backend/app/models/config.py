from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel


class ConfigGroup(str, Enum):
    LLM = "llm"
    EMBEDDING = "embedding"
    MEDIA = "media"
    STORAGE = "storage"
    PAYMENT = "payment"
    EMAIL = "email"
    RECAPTCHA = "recaptcha"
    VOICE = "voice"
    FIREBASE = "firebase"
    MISC = "misc"


class ConfigFieldDefinition(BaseModel):
    key: str
    label: str
    type: str = "text"
    placeholder: Optional[str] = None
    default: Optional[str] = None
    required: bool = False
    secret: bool = False
    description: Optional[str] = None
    options: Optional[list[dict[str, str]]] = None
    model_provider: Optional[str] = None


class ConfigGroupDefinition(BaseModel):
    group: ConfigGroup
    label: str
    description: Optional[str] = None
    fields: list[ConfigFieldDefinition]


CONFIG_DEFINITIONS: list[ConfigGroupDefinition] = [
    ConfigGroupDefinition(
        group=ConfigGroup.LLM,
        label="LLM Settings",
        description="Chat and orchestration LLM provider settings",
        fields=[
            ConfigFieldDefinition(
                key="LLM_PROVIDER",
                label="Provider",
                type="select",
                default="novita",
                options=[
                    {"value": "novita", "label": "Novita"},
                    {"value": "openai", "label": "OpenAI"},
                    {"value": "deepseek", "label": "DeepSeek"},
                    {"value": "ollama", "label": "Ollama (Local)"},
                ],
            ),
            ConfigFieldDefinition(key="LLM_API_KEY", label="API Key", type="password", secret=True),
            ConfigFieldDefinition(
                key="LLM_BASE_URL",
                label="API Base URL",
                type="text",
                default="https://api.novita.ai/openai/v1",
                description="OpenAI-compatible base URL",
            ),
            ConfigFieldDefinition(
                key="LLM_LOCAL_BASE_URL",
                label="Ollama Base URL",
                type="text",
                default="http://127.0.0.1:11434",
            ),
            ConfigFieldDefinition(
                key="LLM_CHAT_MODEL",
                label="Chat Model",
                type="model_select",
                default="meta-llama/llama-3.3-70b-instruct",
            ),
            ConfigFieldDefinition(
                key="LLM_ORCHESTRATOR_MODEL",
                label="Orchestrator Model",
                type="model_select",
                default="sao10k/l3-8b-lunaris",
            ),
            ConfigFieldDefinition(
                key="LLM_INTENT_MODEL",
                label="Intent Model",
                type="model_select",
                default="deepseek/deepseek-v3.2",
            ),
            ConfigFieldDefinition(
                key="LLM_TIMEOUT_SECONDS",
                label="Timeout (seconds)",
                type="number",
                default="300",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.EMBEDDING,
        label="Embedding Settings",
        fields=[
            ConfigFieldDefinition(
                key="EMBEDDING_PROVIDER",
                label="Provider",
                type="select",
                default="cloudflare",
                options=[
                    {"value": "cloudflare", "label": "Cloudflare"},
                    {"value": "openai", "label": "OpenAI"},
                ],
            ),
            ConfigFieldDefinition(
                key="EMBEDDING_MODEL",
                label="Embedding Model",
                default="@cf/qwen/qwen3-embedding-0.6b",
            ),
            ConfigFieldDefinition(key="OPENAI_API_KEY", label="OpenAI API Key", type="password", secret=True),
            ConfigFieldDefinition(key="CF_ACCOUNT_ID", label="Cloudflare Account ID"),
            ConfigFieldDefinition(key="CF_API_TOKEN", label="Cloudflare API Token", type="password", secret=True),
            ConfigFieldDefinition(
                key="CF_EMBEDDING_MODEL",
                label="Cloudflare Embedding Model",
                default="@cf/qwen/qwen3-embedding-0.6b",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.STORAGE,
        label="Storage Settings",
        fields=[
            ConfigFieldDefinition(key="R2_ACCESS_KEY_ID", label="R2 Access Key ID"),
            ConfigFieldDefinition(key="R2_SECRET_ACCESS_KEY", label="R2 Secret Access Key", type="password", secret=True),
            ConfigFieldDefinition(key="R2_BUCKET_NAME", label="R2 Bucket Name", default="aigirl-media"),
            ConfigFieldDefinition(
                key="R2_ENDPOINT_URL",
                label="R2 Endpoint URL",
                placeholder="https://your-account-id.r2.cloudflarestorage.com",
            ),
            ConfigFieldDefinition(key="R2_PUBLIC_URL", label="R2 Public URL"),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.MEDIA,
        label="Media Settings",
        fields=[
            ConfigFieldDefinition(
                key="IMAGE_PROVIDER",
                label="Image Provider",
                type="select",
                default="novita",
                options=[
                    {"value": "novita", "label": "Novita (SDXL)"},
                    {"value": "z_image_turbo_lora", "label": "Novita (Z Image Turbo LoRA)"},
                ],
            ),
            ConfigFieldDefinition(key="NOVITA_API_KEY", label="Novita API Key", type="password", secret=True),
            ConfigFieldDefinition(key="NOVITA_BASE_URL", label="Novita Base URL", default="https://api.novita.ai/v3"),
            ConfigFieldDefinition(
                key="IMAGE_TXT2IMG_MODEL",
                label="txt2img Model",
                type="model_select",
                default="juggernautXL_v9Rdphoto2Lightning_285361.safetensors",
                model_provider="novita_image",
            ),
            ConfigFieldDefinition(
                key="IMAGE_IMG2IMG_MODEL",
                label="img2img Model",
                type="model_select",
                default="juggernautXL_v9Rdphoto2Lightning_285361.safetensors",
                model_provider="novita_image",
            ),
            ConfigFieldDefinition(key="IMG2IMG_STRENGTH", label="img2img Strength", type="number", default="0.7"),
            ConfigFieldDefinition(
                key="IMG2IMG_SAMPLER",
                label="img2img Sampler",
                type="select",
                default="DPM++ 2M",
                options=[
                    {"value": "DPM++ 2M", "label": "DPM++ 2M"},
                    {"value": "DPM++ SDE", "label": "DPM++ SDE"},
                    {"value": "Euler a", "label": "Euler a"},
                    {"value": "Euler", "label": "Euler"},
                    {"value": "DDIM", "label": "DDIM"},
                ],
            ),
            ConfigFieldDefinition(key="IMAGE_DEFAULT_WIDTH", label="Default Width", type="number", default="1024"),
            ConfigFieldDefinition(key="IMAGE_DEFAULT_HEIGHT", label="Default Height", type="number", default="1024"),
            ConfigFieldDefinition(key="IMAGE_DEFAULT_STEPS", label="Default Steps", type="number", default="20"),
            ConfigFieldDefinition(key="IMAGE_DEFAULT_CFG", label="Default CFG", type="number", default="7.5"),
            ConfigFieldDefinition(
                key="VIDEO_PROVIDER",
                label="Video Provider",
                type="select",
                default="novita",
                options=[{"value": "novita", "label": "Novita (Wan)"}],
            ),
            ConfigFieldDefinition(key="VIDEO_MODEL", label="Video Model", default="wan_i2v_22"),
            ConfigFieldDefinition(key="SORA_API_KEY", label="Sora API Key", type="password", secret=True),
            ConfigFieldDefinition(key="SORA_BASE_URL", label="Sora Base URL"),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.PAYMENT,
        label="Payment Settings",
        fields=[
            ConfigFieldDefinition(key="STRIPE_ENABLED", label="Enable Stripe", type="select", default="false"),
            ConfigFieldDefinition(key="STRIPE_SECRET_KEY", label="Stripe Secret Key", type="password", secret=True),
            ConfigFieldDefinition(key="STRIPE_WEBHOOK_SECRET", label="Stripe Webhook Secret", type="password", secret=True),
            ConfigFieldDefinition(key="CCBILL_ENABLED", label="Enable CCBill", type="select", default="false"),
            ConfigFieldDefinition(key="CCBILL_MERCHANT_ID", label="CCBill Merchant ID"),
            ConfigFieldDefinition(key="CCBILL_SUBACCOUNT", label="CCBill Subaccount"),
            ConfigFieldDefinition(key="CCBILL_FLEXFORM_ID", label="CCBill FlexForm ID"),
            ConfigFieldDefinition(key="CCBILL_SALT", label="CCBill Salt", type="password", secret=True),
            ConfigFieldDefinition(key="CCBILL_DATALINK_USERNAME", label="CCBill Datalink Username"),
            ConfigFieldDefinition(key="CCBILL_DATALINK_PASSWORD", label="CCBill Datalink Password", type="password", secret=True),
            ConfigFieldDefinition(key="USDT_PAYMENT_GATEWAY_ENABLED", label="Enable USDT Gateway", type="select", default="false"),
            ConfigFieldDefinition(key="USDT_PAYMENT_GATEWAY_BASE_URL", label="USDT Gateway Base URL"),
            ConfigFieldDefinition(key="USDT_PAYMENT_GATEWAY_API_KEY", label="USDT Gateway API Key", type="password", secret=True),
            ConfigFieldDefinition(
                key="USDT_PAYMENT_GATEWAY_WEBHOOK_AUTH_TOKEN",
                label="USDT Webhook Auth Token",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="TELEGRAM_STAR_GATEWAY_ENABLED",
                label="Enable Telegram Star Gateway",
                type="select",
                default="false",
            ),
            ConfigFieldDefinition(key="TELEGRAM_STAR_GATEWAY_BASE_URL", label="Telegram Star Gateway Base URL"),
            ConfigFieldDefinition(key="TELEGRAM_STAR_GATEWAY_API_TOKEN", label="Telegram Star Gateway API Token", type="password", secret=True),
            ConfigFieldDefinition(
                key="TELEGRAM_STAR_GATEWAY_WEBHOOK_AUTH_TOKEN",
                label="Telegram Star Webhook Auth Token",
                type="password",
                secret=True,
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.EMAIL,
        label="Email Settings",
        fields=[
            ConfigFieldDefinition(key="SMTP_ADDRESS", label="SMTP Host"),
            ConfigFieldDefinition(key="SMTP_USERNAME", label="SMTP Username"),
            ConfigFieldDefinition(key="SMTP_PASSWORD", label="SMTP Password", type="password", secret=True),
            ConfigFieldDefinition(key="SMTP_FROM_EMAIL", label="From Email"),
            ConfigFieldDefinition(key="SMTP_FROM_NAME", label="From Name"),
            ConfigFieldDefinition(key="SMTP_USE_SSL", label="Use SSL", type="select", default="false"),
            ConfigFieldDefinition(key="SMTP_SSL_PORT", label="SSL Port", type="number", default="465"),
            ConfigFieldDefinition(key="SMTP_USE_STARTTLS", label="Use STARTTLS", type="select", default="true"),
            ConfigFieldDefinition(key="SMTP_STARTTLS_PORT", label="STARTTLS Port", type="number", default="587"),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.RECAPTCHA,
        label="reCAPTCHA Settings",
        fields=[
            ConfigFieldDefinition(key="RECAPTCHA_ENABLED", label="Enable reCAPTCHA", type="select", default="false"),
            ConfigFieldDefinition(key="RECAPTCHA_VERSION", label="Version", type="select", default="v3"),
            ConfigFieldDefinition(key="RECAPTCHA_SITE_KEY", label="Site Key"),
            ConfigFieldDefinition(key="RECAPTCHA_SECRET_KEY", label="Secret Key", type="password", secret=True),
            ConfigFieldDefinition(key="RECAPTCHA_MIN_SCORE", label="Min Score", type="number", default="0.5"),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.VOICE,
        label="Voice Settings",
        fields=[
            ConfigFieldDefinition(key="ENABLE_VOICE_RESPONSE", label="Enable Voice Response", type="select", default="true"),
            ConfigFieldDefinition(key="LIVEKIT_API_KEY", label="LiveKit API Key"),
            ConfigFieldDefinition(key="LIVEKIT_API_SECRET", label="LiveKit API Secret", type="password", secret=True),
            ConfigFieldDefinition(key="LIVEKIT_WS_URL", label="LiveKit WebSocket URL"),
            ConfigFieldDefinition(key="ELEVENLABS_API_KEY", label="ElevenLabs API Key", type="password", secret=True),
            ConfigFieldDefinition(key="ELEVENLABS_BASE_URL", label="ElevenLabs Base URL", default="https://api.elevenlabs.io/v1"),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.FIREBASE,
        label="Firebase Settings",
        fields=[
            ConfigFieldDefinition(key="FIREBASE_PROJECT_ID", label="Project ID"),
            ConfigFieldDefinition(key="FIREBASE_CREDENTIALS_PATH", label="Credentials File Path", placeholder="./firebase-credentials.json"),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.MISC,
        label="System Settings",
        fields=[
            ConfigFieldDefinition(key="JWT_SECRET_KEY", label="JWT Secret", type="password", secret=True, required=True),
            ConfigFieldDefinition(key="ADMIN_PASSWORD", label="Admin Password", type="password", secret=True),
            ConfigFieldDefinition(key="ADMIN_EMAILS", label="Admin Emails", default="admin@roxy.ai"),
            ConfigFieldDefinition(key="CORS_ORIGINS", label="CORS Origins", default="http://localhost:5173"),
            ConfigFieldDefinition(key="RATE_LIMIT_PER_MINUTE", label="Rate Limit / Minute", type="number", default="60"),
            ConfigFieldDefinition(key="RATE_LIMIT_PER_HOUR", label="Rate Limit / Hour", type="number", default="1000"),
            ConfigFieldDefinition(
                key="ENVIRONMENT",
                label="Environment",
                type="select",
                default="development",
                options=[
                    {"value": "development", "label": "Development"},
                    {"value": "staging", "label": "Staging"},
                    {"value": "production", "label": "Production"},
                ],
            ),
        ],
    ),
]


CONFIG_KEY_MAP: dict[str, ConfigGroup] = {}
for group_def in CONFIG_DEFINITIONS:
    for field in group_def.fields:
        CONFIG_KEY_MAP[field.key] = group_def.group


class ConfigValue(BaseModel):
    key: str
    value: Optional[str] = None
    masked_value: Optional[str] = None


class ConfigGroupResponse(BaseModel):
    group: ConfigGroup
    label: str
    description: Optional[str] = None
    fields: list[dict[str, Any]]


class ConfigUpdateRequest(BaseModel):
    values: dict[str, str]
