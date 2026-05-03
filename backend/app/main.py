from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager

from app.core.config import get_settings
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)
from app.middleware.security_middleware import RateLimitMiddleware
from app.routers import (
    auth_router,
    chat_router,
    character_router,
    content_router,
    media_router,
    gateway_router,
    gateway_advanced_router,
    billing_router,
    notifications_router,
    admin_router,
    admin_api_key_router,
    legacy_api_key_router,
    admin_api_router,
    config_router,
    preset_router,
    story_router,
    admin_story_router,
    state_router,
    pipeline_router,
    ugc_router,
    templates_router,
    blog_router,
    geo_router,
    telegram_auth_router,
    creators_router,
    support_router,
    admin_support_router,
    telegram_bot_router,
    ops_router,
    admin_ops_router,
    world_character_router,
    world_story_router,
    world_context_router,
    world_relationship_router,
    scripts_router,
    memory_router,
    inference_router,
    voices_router,
    rewards_router,
)
from app.routers.script_library import router as script_library_router
from app.routers.admin.prompts import router as admin_prompts_router
from app.routers.admin.scripts import router as admin_scripts_router
from app.routers.admin.credits import router as admin_credits_router
from app.routers.admin.audit import router as admin_audit_router
from app.routers.admin.loras import router as admin_loras_router
from app.routers.admin.script_library import router as admin_script_library_router
from app.routers.openpose_presets import (
    admin_router as admin_openpose_presets_router,
    public_router as openpose_presets_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"Starting {settings.app_name}...")
    
    security_warnings = settings.validate_security_settings()
    for warning in security_warnings:
        print(f"SECURITY WARNING: {warning}")
    
    from app.core.database import db
    from app.core.redis_client import redis_client
    
    try:
        await db.connect()
        print("Database connected")
    except Exception as e:
        print(f"Database connection failed: {e}")
    
    try:
        await redis_client.connect()
        print("Redis connected")
    except Exception as e:
        print(f"Redis connection failed (optional): {e}")
    
    try:
        from app.services.prompt_template_service import prompt_template_service
        await prompt_template_service.initialize_defaults()
        print("Default prompt templates initialized")
    except Exception as e:
        print(f"Failed to initialize prompt templates: {e}")
    
    try:
        from app.services.config_preset_service import ConfigPresetService
        preset_service = ConfigPresetService()
        count = await preset_service.init_builtin_presets()
        if count > 0:
            print(f"Initialized {count} builtin config presets")
    except Exception as e:
        print(f"Failed to initialize config presets: {e}")
    
    try:
        from app.services.config_service import ConfigService
        config_service = ConfigService()
        migrated = await config_service.migrate_from_redis()
        if migrated > 0:
            print(f"Migrated {migrated} config values from Redis to database")
        defaults = await config_service.init_defaults()
        if defaults > 0:
            print(f"Initialized {defaults} default config values")
    except Exception as e:
        print(f"Failed to migrate/initialize config: {e}")
    
    try:
        from app.services.media_service import MediaService
        await MediaService.get_instance().refresh_providers()
        print("Media providers initialized from admin config")
    except Exception as e:
        print(f"Failed to initialize media providers: {e}")

    try:
        from app.services.llm_service import LLMService
        await LLMService.get_instance().refresh_providers()
        print("LLM providers initialized from admin config")
    except Exception as e:
        print(f"Failed to initialize LLM providers: {e}")

    try:
        from app.services.scheduler_service import start_scheduler
        start_scheduler()
        print("Scheduler started")
    except Exception as e:
        print(f"Failed to start scheduler: {e}")
    
    yield
    
    try:
        from app.services.scheduler_service import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass
    
    try:
        await redis_client.disconnect()
    except Exception:
        pass
    
    print("Shutting down...")


app = FastAPI(
    title="Roxy API",
    description="Backend API for Roxy - AI Character Chat Platform",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=[
        "X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Limit",
        "X-Transcript-In", "X-Transcript-Out", "X-Emotion",
        "X-Credits-Used", "X-Session-Total-Seconds",
    ],
    max_age=600,
)

app.add_middleware(RateLimitMiddleware)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(character_router)
app.include_router(content_router)
app.include_router(media_router)
app.include_router(gateway_router)
app.include_router(gateway_advanced_router)
app.include_router(billing_router)
app.include_router(notifications_router)
app.include_router(admin_router)
app.include_router(admin_api_key_router)
app.include_router(legacy_api_key_router)
app.include_router(admin_api_router)
app.include_router(config_router)
app.include_router(preset_router)
app.include_router(story_router)
app.include_router(admin_story_router)
app.include_router(state_router)
app.include_router(pipeline_router)
app.include_router(ugc_router)
app.include_router(templates_router)
app.include_router(blog_router)
app.include_router(geo_router)
app.include_router(telegram_auth_router)
app.include_router(creators_router)
app.include_router(support_router)
app.include_router(admin_support_router)
app.include_router(telegram_bot_router)
app.include_router(ops_router)
app.include_router(admin_ops_router)
app.include_router(world_character_router)
app.include_router(world_story_router)
app.include_router(world_context_router)
app.include_router(world_relationship_router)
app.include_router(scripts_router)
app.include_router(script_library_router)
app.include_router(admin_prompts_router)
app.include_router(admin_scripts_router)
app.include_router(admin_credits_router)
app.include_router(admin_audit_router)
app.include_router(admin_loras_router)
app.include_router(admin_script_library_router)
app.include_router(openpose_presets_router)
app.include_router(admin_openpose_presets_router)
app.include_router(memory_router)
app.include_router(inference_router)
app.include_router(voices_router)
app.include_router(rewards_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
