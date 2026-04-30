from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
from enum import Enum
import re


class SubscriptionTier(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"


class CreditPackType(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CharacterGender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class StoryStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseResponse(BaseModel):
    success: bool = True
    message: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            pass
        if not any(c.islower() for c in v):
            pass
        return v


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=2, max_length=50)
    
    @field_validator('display_name')
    @classmethod
    def sanitize_display_name(cls, v):
        v = re.sub(r'<[^>]*>', '', v)
        return v.strip()


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class FirebaseTokenRequest(BaseModel):
    token: str = Field(..., min_length=1)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


from typing import Generic, TypeVar

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class User(BaseModel):
    id: str
    email: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    credits: float = 0
    is_admin: bool = False
    telegram_id: str | None = None
    telegram_username: str | None = None
    telegram_bound_at: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class UserProfile(BaseModel):
    display_name: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    preferences: dict[str, Any] | None = None


class Character(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None
    personality: str | None = None
    backstory: str | None = None
    gender: CharacterGender | None = None
    avatar_url: str | None = None
    cover_url: str | None = None
    greeting: str | None = None
    system_prompt: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_official: bool = False
    is_public: bool = True
    creator_id: str | None = None
    family_id: str | None = None
    voice_id: str | None = None
    lora_status: TaskStatus | None = None
    created_at: datetime
    updated_at: datetime | None = None


class CharacterCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    personality: str | None = None
    backstory: str | None = None
    gender: CharacterGender | None = None
    avatar_url: str | None = None
    cover_url: str | None = None
    greeting: str | None = None
    system_prompt: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_public: bool = True


class CharacterUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    personality: str | None = None
    backstory: str | None = None
    gender: CharacterGender | None = None
    avatar_url: str | None = None
    cover_url: str | None = None
    greeting: str | None = None
    system_prompt: str | None = None
    tags: list[str] | None = None
    is_public: bool | None = None


class Story(BaseModel):
    id: str
    title: str
    slug: str | None = None
    description: str | None = None
    character_id: str
    status: StoryStatus = StoryStatus.DRAFT
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    creator_id: str | None = None
    is_public: bool = True
    created_at: datetime
    updated_at: datetime | None = None


class StoryCreate(BaseModel):
    title: str
    slug: str | None = None
    description: str | None = None
    character_id: str
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    is_public: bool = True


class StoryUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    nodes: list[dict[str, Any]] | None = None
    is_public: bool | None = None


class ChatSession(BaseModel):
    id: str
    user_id: str
    character_id: str
    title: str | None = None
    style: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime | None = None


class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    audio_url: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ChatStreamRequest(BaseModel):
    session_id: str | None = None
    character_id: str
    message: str
    style: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class GroupChatStreamRequest(BaseModel):
    session_id: str | None = None
    participants: list[str] = Field(..., min_length=2, max_length=5)
    message: str
    style: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class ChatCompleteRequest(BaseModel):
    character_id: str
    messages: list[dict[str, str]]
    max_tokens: int = 500
    temperature: float = 0.7


class ImageGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str | None = None
    width: int = 512
    height: int = 512
    character_id: str | None = None
    style: str | None = None
    num_images: int = 1


class VoiceGenerateRequest(BaseModel):
    text: str
    character_id: str
    voice_id: str | None = None
    speed: float = 1.0


class SubscriptionCheckoutRequest(BaseModel):
    tier: SubscriptionTier
    success_url: str
    cancel_url: str


class CreditPackCheckoutRequest(BaseModel):
    pack_type: CreditPackType
    success_url: str
    cancel_url: str


class USDTOrderCreate(BaseModel):
    amount: float
    product_id: str
    credits: int | None = None
    pack_id: str | None = None
    network: str | None = None
    metadata: dict[str, Any] | None = None


class CryptoOrderCreate(BaseModel):
    asset: str = "USDT"
    network: str = "TRC20"
    product_type: str = "credit_pack"
    pack_id: str | None = None
    tier: str | None = None
    billing_period: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("asset")
    @classmethod
    def normalize_asset(cls, v: str):
        asset = (v or "").upper()
        if asset not in {"USDT", "USDC"}:
            raise ValueError("asset must be USDT or USDC")
        return asset

    @field_validator("network")
    @classmethod
    def normalize_network(cls, v: str):
        network = (v or "").upper()
        if network not in {"TRC20", "ERC20", "BEP20", "POLYGON", "SOLANA"}:
            raise ValueError("network must be TRC20, ERC20, BEP20, POLYGON, or SOLANA")
        return network


class TelegramStarsOrderCreate(BaseModel):
    amount_stars: int | None = None
    amount: int | None = None
    credits: int | None = None
    product_type: str | None = None
    tier: str | None = None
    billing_period: str | None = None
    product_id: str | None = None
    pack_id: str | None = None
    title: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("amount", "amount_stars")
    @classmethod
    def validate_amount(cls, v: int | None):
        if v is not None and v <= 0:
            raise ValueError("amount must be > 0")
        return v

    @field_validator("credits")
    @classmethod
    def validate_credits(cls, v: int | None):
        if v is not None and v <= 0:
            raise ValueError("credits must be > 0")
        return v


class SupportTicketCreate(BaseModel):
    subject: str
    message: str
    category: str | None = None
    priority: str | None = None


class SupportTicketFeedback(BaseModel):
    rating: int
    comment: str | None = None


class MemoryCorrectRequest(BaseModel):
    old_memory: str
    new_memory: str


class MemoryForgetRequest(BaseModel):
    memory_ids: list[str]


class RelationshipConsentRequest(BaseModel):
    consent_type: str
    granted: bool


class APIKeyCreate(BaseModel):
    name: str
    permissions: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None


class PromptTemplate(BaseModel):
    name: str
    content: str
    description: str | None = None
    variables: list[str] = Field(default_factory=list)
    hints: dict[str, str] = Field(default_factory=dict)


class PromptTestRequest(BaseModel):
    variables: dict[str, Any] = Field(default_factory=dict)


class BatchGenerateRequest(BaseModel):
    template_id: str
    variables: list[dict[str, Any]]
    callback_url: str | None = None


class SEOGGenerateRequest(BaseModel):
    keywords: list[str]
    template_id: str


class Task(BaseModel):
    id: str
    type: str
    status: TaskStatus
    progress: float = 0.0
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class NotificationSubscribe(BaseModel):
    endpoint: str
    keys: dict[str, str]


class PushNotification(BaseModel):
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)


class UGCCharacterCreate(BaseModel):
    name: str
    description: str | None = None
    personality: str | None = None
    backstory: str | None = None
    gender: CharacterGender | None = None
    avatar_url: str | None = None
    greeting: str | None = None
    system_prompt: str | None = None
    tags: list[str] = Field(default_factory=list)


class UGCScriptCreate(BaseModel):
    title: str
    description: str | None = None
    content: str
    template_id: str | None = None


class BlogPostCreate(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: str | None = None
    featured_image: str | None = None
    tags: list[str] = Field(default_factory=list)
    is_published: bool = False


class BlogPostUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    content: str | None = None
    excerpt: str | None = None
    featured_image: str | None = None
    tags: list[str] | None = None
    is_published: bool | None = None
