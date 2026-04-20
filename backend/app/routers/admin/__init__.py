from app.routers.admin.prompts import router as admin_prompts_router
from app.routers.admin.scripts import router as admin_scripts_router
from app.routers.admin.credits import router as admin_credits_router
from app.routers.admin.audit import router as admin_audit_router
from app.routers.admin.script_library import router as admin_script_library_router
from app.routers.admin_main import (
    router,
    admin_api_key_router,
    legacy_api_key_router,
    admin_api_router,
    config_router,
    preset_router,
)

__all__ = [
    "admin_prompts_router",
    "admin_scripts_router",
    "admin_credits_router",
    "admin_audit_router",
    "admin_script_library_router",
    "router",
    "admin_api_key_router",
    "legacy_api_key_router",
    "admin_api_router",
    "config_router",
    "preset_router",
]
