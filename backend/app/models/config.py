from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


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
        label="LLM 配置",
        description="大语言模型 API 配置",
        fields=[
            ConfigFieldDefinition(
                key="LLM_PROVIDER",
                label="LLM 提供商",
                type="select",
                default="novita",
                description="选择 LLM 服务提供商",
                options=[
                    {"value": "novita", "label": "Novita"},
                    {"value": "openai", "label": "OpenAI"},
                    {"value": "deepseek", "label": "DeepSeek"},
                    {"value": "ollama", "label": "Ollama (本地)"},
                ],
            ),
            ConfigFieldDefinition(
                key="LLM_API_KEY",
                label="API Key",
                type="password",
                secret=True,
                description="当前提供商的 API 密钥",
            ),
            ConfigFieldDefinition(
                key="LLM_LOCAL_BASE_URL",
                label="Ollama 服务地址",
                type="text",
                default="http://127.0.0.1:11434",
                description="本地 Ollama 服务 URL (仅 Ollama 提供商需要)",
            ),
            ConfigFieldDefinition(
                key="LLM_CHAT_MODEL",
                label="聊天模型",
                type="model_select",
                default="google/gemma-4-26b-a4b-it",
                description="聊天使用的模型",
            ),
            ConfigFieldDefinition(
                key="LLM_ORCHESTRATOR_MODEL",
                label="编排模型",
                type="model_select",
                default="google/gemma-4-26b-a4b-it",
                description="编排使用的模型",
            ),
            ConfigFieldDefinition(
                key="LLM_INTENT_MODEL",
                label="意图识别模型",
                type="model_select",
                default="google/gemma-4-26b-a4b-it",
                description="意图识别使用的模型",
            ),
            ConfigFieldDefinition(
                key="LLM_TIMEOUT_SECONDS",
                label="超时时间(秒)",
                type="number",
                default="300",
                description="LLM 请求超时时间",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.EMBEDDING,
        label="Embedding 配置",
        description="向量嵌入服务配置",
        fields=[
            ConfigFieldDefinition(
                key="EMBEDDING_PROVIDER",
                label="Embedding 提供商",
                type="select",
                default="cloudflare",
                description="选择 embedding 服务提供商 (cloudflare/openai)",
                options=[
                    {"value": "cloudflare", "label": "Cloudflare"},
                    {"value": "openai", "label": "OpenAI"},
                ],
            ),
            ConfigFieldDefinition(
                key="EMBEDDING_MODEL",
                label="Embedding 模型",
                type="text",
                default="@cf/qwen/qwen3-embedding-0.6b",
            ),
            ConfigFieldDefinition(
                key="OPENAI_API_KEY",
                label="OpenAI API Key",
                type="password",
                secret=True,
                description="OpenAI API 密钥",
            ),
            ConfigFieldDefinition(
                key="CF_ACCOUNT_ID",
                label="Cloudflare Account ID",
                type="text",
            ),
            ConfigFieldDefinition(
                key="CF_API_TOKEN",
                label="Cloudflare API Token",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="CF_EMBEDDING_MODEL",
                label="CF Embedding 模型",
                type="text",
                default="@cf/qwen/qwen3-embedding-0.6b",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.STORAGE,
        label="存储配置 (R2)",
        description="Cloudflare R2 对象存储配置",
        fields=[
            ConfigFieldDefinition(
                key="R2_ACCESS_KEY_ID",
                label="R2 Access Key ID",
                type="text",
            ),
            ConfigFieldDefinition(
                key="R2_SECRET_ACCESS_KEY",
                label="R2 Secret Access Key",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="R2_BUCKET_NAME",
                label="R2 Bucket 名称",
                type="text",
                default="aigirl-media",
            ),
            ConfigFieldDefinition(
                key="R2_ENDPOINT_URL",
                label="R2 Endpoint URL",
                type="text",
                placeholder="https://your-account-id.r2.cloudflarestorage.com",
            ),
            ConfigFieldDefinition(
                key="R2_PUBLIC_URL",
                label="R2 公开 URL",
                type="text",
                placeholder="https://your-cdn-url.com",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.MEDIA,
        label="媒体生成配置",
        description="图片和视频生成服务配置",
        fields=[
            ConfigFieldDefinition(
                key="IMAGE_PROVIDER",
                label="图片生成提供商",
                type="select",
                default="novita",
                description="选择图片生成服务提供商",
                options=[
                    {"value": "novita", "label": "Novita (SDXL)"},
                    {"value": "z_image_turbo_lora", "label": "Novita (Z Image Turbo LoRA)"},
                ],
            ),
            ConfigFieldDefinition(
                key="NOVITA_API_KEY",
                label="Novita API Key",
                type="password",
                secret=True,
                description="Novita 图片/视频生成 API Key",
            ),
            ConfigFieldDefinition(
                key="NOVITA_BASE_URL",
                label="Novita Base URL",
                type="text",
                default="https://api.novita.ai/v3",
            ),
            ConfigFieldDefinition(
                key="IMAGE_TXT2IMG_MODEL",
                label="txt2img 模型",
                type="model_select",
                default="juggernautXL_v9Rdphoto2Lightning_285361.safetensors",
                description="文本生成图片使用的模型",
                model_provider="novita_image",
            ),
            ConfigFieldDefinition(
                key="IMAGE_IMG2IMG_MODEL",
                label="img2img 模型",
                type="model_select",
                default="juggernautXL_v9Rdphoto2Lightning_285361.safetensors",
                description="图片生成图片使用的模型",
                model_provider="novita_image",
            ),
            ConfigFieldDefinition(
                key="IMG2IMG_STRENGTH",
                label="img2img Strength",
                type="number",
                default="0.7",
                description="原图保留程度 (0-1，越小保留越多)",
            ),
            ConfigFieldDefinition(
                key="IMG2IMG_SAMPLER",
                label="img2img Sampler",
                type="select",
                default="DPM++ 2M",
                description="img2img 采样器",
                options=[
                    {"value": "DPM++ 2M", "label": "DPM++ 2M"},
                    {"value": "DPM++ SDE", "label": "DPM++ SDE"},
                    {"value": "Euler a", "label": "Euler a"},
                    {"value": "Euler", "label": "Euler"},
                    {"value": "DDIM", "label": "DDIM"},
                ],
            ),
            ConfigFieldDefinition(
                key="IMAGE_DEFAULT_WIDTH",
                label="默认图片宽度",
                type="number",
                default="1024",
                description="生成图片的默认宽度",
            ),
            ConfigFieldDefinition(
                key="IMAGE_DEFAULT_HEIGHT",
                label="默认图片高度",
                type="number",
                default="1024",
                description="生成图片的默认高度",
            ),
            ConfigFieldDefinition(
                key="IMAGE_DEFAULT_STEPS",
                label="默认步数",
                type="number",
                default="20",
                description="生成图片的默认采样步数",
            ),
            ConfigFieldDefinition(
                key="IMAGE_DEFAULT_CFG",
                label="默认 CFG Scale",
                type="number",
                default="7.5",
                description="提示词相关性 (Classifier-Free Guidance)",
            ),
            ConfigFieldDefinition(
                key="VIDEO_PROVIDER",
                label="视频生成提供商",
                type="select",
                default="novita",
                description="选择视频生成服务提供商",
                options=[
                    {"value": "novita", "label": "Novita (Wan)"},
                    {"value": "sora", "label": "OpenAI Sora"},
                ],
            ),
            ConfigFieldDefinition(
                key="VIDEO_MODEL",
                label="视频生成模型",
                type="select",
                default="wan_i2v_22",
                description="视频生成使用的模型",
                options=[
                    {"value": "wan_i2v_22", "label": "Wan I2V 22"},
                ],
            ),
            ConfigFieldDefinition(
                key="SORA_API_KEY",
                label="Sora API Key",
                type="password",
                secret=True,
                description="OpenAI Sora API Key",
            ),
            ConfigFieldDefinition(
                key="SORA_BASE_URL",
                label="Sora Base URL",
                type="text",
                placeholder="https://api.openai.com/v1",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.PAYMENT,
        label="支付配置",
        description="支付网关配置",
        fields=[
            ConfigFieldDefinition(
                key="CCBILL_ENABLED",
                label="CCBill 启用",
                type="boolean",
                default="false",
            ),
            ConfigFieldDefinition(
                key="CCBILL_MERCHANT_ID",
                label="CCBill Merchant ID",
                type="text",
            ),
            ConfigFieldDefinition(
                key="CCBILL_SUBACCOUNT",
                label="CCBill Subaccount",
                type="text",
                default="0000",
            ),
            ConfigFieldDefinition(
                key="CCBILL_FLEXFORM_ID",
                label="CCBill FlexForm ID",
                type="text",
            ),
            ConfigFieldDefinition(
                key="CCBILL_SALT",
                label="CCBill Salt",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="CCBILL_DATALINK_USERNAME",
                label="CCBill Datalink Username",
                type="text",
            ),
            ConfigFieldDefinition(
                key="CCBILL_DATALINK_PASSWORD",
                label="CCBill Datalink Password",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="USDT_PAYMENT_GATEWAY_ENABLED",
                label="USDT 支付启用",
                type="boolean",
                default="false",
            ),
            ConfigFieldDefinition(
                key="USDT_PAYMENT_GATEWAY_BASE_URL",
                label="USDT Gateway URL",
                type="text",
            ),
            ConfigFieldDefinition(
                key="USDT_PAYMENT_GATEWAY_API_KEY",
                label="USDT Gateway API Key",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="USDT_PAYMENT_GATEWAY_WEBHOOK_AUTH_TOKEN",
                label="USDT Webhook Token",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="TELEGRAM_STAR_GATEWAY_ENABLED",
                label="Telegram Stars 启用",
                type="boolean",
                default="false",
            ),
            ConfigFieldDefinition(
                key="TELEGRAM_STAR_GATEWAY_BASE_URL",
                label="Telegram Stars Gateway URL",
                type="text",
            ),
            ConfigFieldDefinition(
                key="TELEGRAM_STAR_GATEWAY_API_TOKEN",
                label="Telegram Stars API Token",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="TELEGRAM_STAR_GATEWAY_WEBHOOK_AUTH_TOKEN",
                label="Telegram Stars Webhook Token",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="STRIPE_ENABLED",
                label="Stripe 启用",
                type="boolean",
                default="false",
            ),
            ConfigFieldDefinition(
                key="STRIPE_SECRET_KEY",
                label="Stripe Secret Key",
                type="password",
                secret=True,
                description="Stripe Secret Key (sk_live_...)",
            ),
            ConfigFieldDefinition(
                key="STRIPE_WEBHOOK_SECRET",
                label="Stripe Webhook Secret",
                type="password",
                secret=True,
                description="Stripe Webhook Signing Secret",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.EMAIL,
        label="邮件配置 (SMTP)",
        description="SMTP 邮件服务配置",
        fields=[
            ConfigFieldDefinition(
                key="SMTP_ADDRESS",
                label="SMTP 服务器地址",
                type="text",
                default="smtp.larksuite.com",
            ),
            ConfigFieldDefinition(
                key="SMTP_SSL_PORT",
                label="SSL 端口",
                type="number",
                default="465",
            ),
            ConfigFieldDefinition(
                key="SMTP_STARTTLS_PORT",
                label="STARTTLS 端口",
                type="number",
                default="587",
            ),
            ConfigFieldDefinition(
                key="SMTP_USE_SSL",
                label="使用 SSL",
                type="boolean",
                default="true",
            ),
            ConfigFieldDefinition(
                key="SMTP_USE_STARTTLS",
                label="使用 STARTTLS",
                type="boolean",
                default="false",
            ),
            ConfigFieldDefinition(
                key="SMTP_USERNAME",
                label="SMTP 用户名",
                type="text",
            ),
            ConfigFieldDefinition(
                key="SMTP_PASSWORD",
                label="SMTP 密码",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="SMTP_FROM_EMAIL",
                label="发件人邮箱",
                type="text",
            ),
            ConfigFieldDefinition(
                key="SMTP_FROM_NAME",
                label="发件人名称",
                type="text",
                default="AIGirl Admin",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.RECAPTCHA,
        label="reCAPTCHA 配置",
        description="Google reCAPTCHA 验证配置",
        fields=[
            ConfigFieldDefinition(
                key="RECAPTCHA_ENABLED",
                label="启用 reCAPTCHA",
                type="boolean",
                default="true",
            ),
            ConfigFieldDefinition(
                key="RECAPTCHA_SECRET_KEY",
                label="Secret Key",
                type="password",
                secret=True,
            ),
            ConfigFieldDefinition(
                key="RECAPTCHA_SITE_KEY",
                label="Site Key",
                type="text",
            ),
            ConfigFieldDefinition(
                key="RECAPTCHA_VERSION",
                label="版本",
                type="select",
                default="v3",
                options=[
                    {"value": "v2", "label": "v2"},
                    {"value": "v3", "label": "v3"},
                ],
            ),
            ConfigFieldDefinition(
                key="RECAPTCHA_MIN_SCORE",
                label="最低分数",
                type="number",
                default="0.5",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.VOICE,
        label="语音配置",
        description="语音服务配置",
        fields=[
            ConfigFieldDefinition(
                key="ENABLE_VOICE_RESPONSE",
                label="启用语音响应",
                type="boolean",
                default="false",
            ),
            ConfigFieldDefinition(
                key="LIVEKIT_API_KEY",
                label="LiveKit API Key",
                type="text",
                description="LiveKit 视频通话 API Key",
            ),
            ConfigFieldDefinition(
                key="LIVEKIT_API_SECRET",
                label="LiveKit API Secret",
                type="password",
                secret=True,
                description="LiveKit API Secret",
            ),
            ConfigFieldDefinition(
                key="LIVEKIT_WS_URL",
                label="LiveKit WebSocket URL",
                type="text",
                placeholder="wss://livekit.example.com",
                description="LiveKit WebSocket 连接 URL",
            ),
            ConfigFieldDefinition(
                key="ELEVENLABS_API_KEY",
                label="ElevenLabs API Key",
                type="password",
                secret=True,
                description="ElevenLabs 语音合成 API 密钥",
            ),
            ConfigFieldDefinition(
                key="ELEVENLABS_BASE_URL",
                label="ElevenLabs Base URL",
                type="text",
                default="https://api.elevenlabs.io/v1",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.FIREBASE,
        label="Firebase 配置",
        description="Firebase 认证配置",
        fields=[
            ConfigFieldDefinition(
                key="FIREBASE_PROJECT_ID",
                label="Project ID",
                type="text",
            ),
            ConfigFieldDefinition(
                key="FIREBASE_CREDENTIALS_PATH",
                label="Credentials 文件路径",
                type="text",
                placeholder="./firebase-credentials.json",
            ),
        ],
    ),
    ConfigGroupDefinition(
        group=ConfigGroup.MISC,
        label="系统安全配置",
        description="JWT、管理员、CORS 等系统安全配置",
        fields=[
            ConfigFieldDefinition(
                key="JWT_SECRET_KEY",
                label="JWT 签名密钥",
                type="password",
                secret=True,
                required=True,
                description="JWT 签名密钥 (建议32位以上随机字符串)",
            ),
            ConfigFieldDefinition(
                key="ADMIN_PASSWORD",
                label="管理员登录密码",
                type="password",
                secret=True,
                description="管理员后台登录密码",
            ),
            ConfigFieldDefinition(
                key="ADMIN_EMAILS",
                label="管理员邮箱",
                type="text",
                default="admin@roxy.ai",
                description="管理员邮箱 (多个邮箱用逗号分隔)",
            ),
            ConfigFieldDefinition(
                key="CORS_ORIGINS",
                label="允许的 CORS 域名",
                type="text",
                default="http://localhost:5173",
                description="允许的 CORS 域名 (多个域名用逗号分隔)",
            ),
            ConfigFieldDefinition(
                key="RATE_LIMIT_PER_MINUTE",
                label="每分钟速率限制",
                type="number",
                default="60",
                description="每个 IP 每分钟最大请求数",
            ),
            ConfigFieldDefinition(
                key="RATE_LIMIT_PER_HOUR",
                label="每小时速率限制",
                type="number",
                default="1000",
                description="每个 IP 每小时最大请求数",
            ),
            ConfigFieldDefinition(
                key="ENVIRONMENT",
                label="运行环境",
                type="select",
                default="development",
                description="系统运行环境",
                options=[
                    {"value": "development", "label": "开发 (Development)"},
                    {"value": "staging", "label": "测试 (Staging)"},
                    {"value": "production", "label": "生产 (Production)"},
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
