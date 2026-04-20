from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.routers.character import router as character_router
from app.routers.content import router as content_router
from app.routers.media import router as media_router
from app.routers.gateway import router as gateway_router, router_advanced as gateway_advanced_router
from app.routers.billing import router as billing_router
from app.routers.notifications import router as notifications_router
from app.routers.admin import (
    router as admin_router,
    admin_api_key_router,
    legacy_api_key_router,
    admin_api_router,
    config_router,
    preset_router,
)
from app.routers.story import router as story_router, admin_story_router
from app.routers.state import router as state_router
from app.routers.pipeline import router as pipeline_router
from app.routers.ugc import router as ugc_router
from app.routers.integration import (
    templates_router,
    blog_router,
    geo_router,
    auth_router as telegram_auth_router,
    creators_router,
)
from app.routers.support import router as support_router, admin_support_router
from app.routers.ops import router as ops_router, admin_ops_router
from app.routers.world import (
    character_router as world_character_router,
    story_router as world_story_router,
    context_router as world_context_router,
    relationship_router as world_relationship_router,
)
from app.routers.scripts import router as scripts_router
from app.routers.memory import router as memory_router
from app.routers.inference import router as inference_router
from app.routers.voices import router as voices_router

__all__ = [
    "auth_router",
    "chat_router",
    "character_router",
    "content_router",
    "media_router",
    "gateway_router",
    "gateway_advanced_router",
    "billing_router",
    "notifications_router",
    "admin_router",
    "admin_api_key_router",
    "legacy_api_key_router",
    "admin_api_router",
    "story_router",
    "admin_story_router",
    "state_router",
    "pipeline_router",
    "ugc_router",
    "templates_router",
    "blog_router",
    "geo_router",
    "telegram_auth_router",
    "creators_router",
    "support_router",
    "admin_support_router",
    "ops_router",
    "admin_ops_router",
    "world_character_router",
    "world_story_router",
    "world_context_router",
    "world_relationship_router",
    "scripts_router",
    "config_router",
    "memory_router",
    "inference_router",
    "voices_router",
]
