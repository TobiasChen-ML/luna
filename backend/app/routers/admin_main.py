from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends, Response
from typing import Any, Optional
import hashlib
import secrets
import hmac

from app.models import (
    BaseResponse, Character, CharacterCreate, CharacterUpdate,
    Story, StoryCreate, StoryUpdate, Task, TaskStatus, User,
    CharacterFromTemplate
)
from app.core.dependencies import verify_admin_token, get_admin_user
from app.core.config import get_settings, Settings
from app.core.auth_cookies import set_auth_cookies, clear_auth_cookies
from app.services.auth_service import jwt_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/login")
async def admin_login_page(request: Request) -> dict[str, Any]:
    return {"page": "login", "message": "Admin login page"}


@router.post("/login")
async def admin_login(
    request: Request,
    response: Response,
    data: dict[str, Any],
    settings: Settings = Depends(get_settings)
) -> dict[str, Any]:
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    if email not in settings.admin_emails:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    admin_password = settings.get_admin_password()
    if not admin_password:
        raise HTTPException(
            status_code=503, 
            detail="Admin login is disabled. Please configure ADMIN_PASSWORD."
        )
    
    if not hmac.compare_digest(password, admin_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user_id = hashlib.sha256(email.encode()).hexdigest()[:16]
    token = jwt_service.create_access_token(
        user_id, email, is_admin=True, expires_delta=timedelta(hours=8)
    )
    refresh_token = jwt_service.create_refresh_token(user_id)

    set_auth_cookies(response, token, refresh_token, access_token_max_age=8 * 3600)
    
    return {
        "success": True,
        "access_token": token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "redirect": "/admin/dashboard",
    }


@router.post("/logout")
async def admin_logout(response: Response) -> dict[str, Any]:
    clear_auth_cookies(response)
    return {"success": True, "message": "Logged out"}


@router.post("/login/send-code", response_model=BaseResponse)
async def send_login_code(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Verification code sent")


@router.post("/login/verify-code")
async def verify_login_code(request: Request, data: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": True,
        "token": "admin_token_xyz",
    }


@router.post("/login/resend-code", response_model=BaseResponse)
async def resend_login_code(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="Code resent")


admin_api_key_router = APIRouter(prefix="/api/admin/api-keys", tags=["admin-api-keys"])


@admin_api_key_router.post("")
async def create_api_key(
    request: Request, 
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    return {
        "id": "key_001",
        "name": data.get("name", "New Key"),
        "key": "sk_live_xxxxxxxxxxxx",
        "created_at": datetime.now().isoformat(),
    }


@admin_api_key_router.get("")
async def list_api_keys(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    return [
        {
            "id": "key_001",
            "name": "Production Key",
            "created_at": datetime.now().isoformat(),
        }
    ]


@admin_api_key_router.delete("/{key_id}", response_model=BaseResponse)
async def delete_api_key(
    request: Request, 
    key_id: str,
    admin: User = Depends(get_admin_user)
) -> BaseResponse:
    return BaseResponse(success=True, message="API key deleted")


legacy_api_key_router = APIRouter(prefix="/api/admin/api-keys-legacy", tags=["admin-api-keys-legacy"])


@legacy_api_key_router.get("")
async def list_api_keys_legacy(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    return [
        {
            "id": "key_001",
            "name": "Production Key",
            "created_at": datetime.now().isoformat(),
        }
    ]


@legacy_api_key_router.post("")
async def create_api_key_legacy(
    request: Request, 
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    return {
        "id": "key_001",
        "name": data.get("name", "New Key"),
        "key": "sk_live_xxxxxxxxxxxx",
    }


@legacy_api_key_router.post("/{key_id}/revoke", response_model=BaseResponse)
async def revoke_api_key(
    request: Request, 
    key_id: str,
    admin: User = Depends(get_admin_user)
) -> BaseResponse:
    return BaseResponse(success=True, message="API key revoked")


@router.get("/characters")
async def list_characters_admin(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    top_category: str = "",
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.character_service import character_service
    
    characters, total = await character_service.list_characters(
        page=page,
        page_size=page_size,
        top_category=top_category if top_category else None,
        is_official=True,
        search=search if search else None,
        order_by="created_at DESC",
    )
    
    return {
        "characters": characters,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/characters/{character_id}")
async def get_character_admin(
    request: Request, 
    character_id: str,
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.character_service import character_service
    
    character = await character_service.get_character_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return character


@router.get("/characters/{character_id}/edit")
async def edit_character_page(
    request: Request, 
    character_id: str,
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.character_service import character_service
    
    character = await character_service.get_character_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return {
        "page": "edit_character",
        "character_id": character_id,
        "character": character,
    }


@router.post("/characters/create")
async def create_character_admin(
    request: Request,
    data: dict[str, Any],
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.character_service import character_service
    from app.models.character import CharacterCreate
    
    character_create = CharacterCreate(**data)
    character = await character_service.create_character(character_create)
    
    return character


@router.post("/characters/{character_id}/ai-fill", response_model=BaseResponse)
async def ai_fill_character(
    request: Request, 
    character_id: str,
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    from app.services.character_factory import character_factory
    
    try:
        character = await character_factory.regenerate_images(character_id)
        return BaseResponse(success=True, message=f"AI fill completed for {character.get('name')}")
    except Exception as e:
        return BaseResponse(success=False, message=str(e))


@router.post("/characters/{character_id}/update")
async def update_character_admin(
    request: Request, 
    character_id: str, 
    data: dict[str, Any],
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.character_service import character_service
    from app.models.character import CharacterUpdate
    
    update_data = CharacterUpdate(**data)
    character = await character_service.update_character(character_id, update_data)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return character


@router.post("/characters/{character_id}/delete", response_model=BaseResponse)
async def delete_character_admin(
    request: Request, 
    character_id: str,
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    from app.services.character_service import character_service
    
    success = await character_service.delete_character(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return BaseResponse(success=True, message="Character deleted")


admin_api_router = APIRouter(prefix="/api/admin/api", tags=["admin-api"])


@admin_api_router.post("/characters/batch-delete", response_model=BaseResponse)
async def batch_delete_characters(
    request: Request, 
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> BaseResponse:
    from app.services.character_service import character_service
    
    ids = data.get("ids", [])
    if not ids:
        return BaseResponse(success=False, message="No IDs provided")
    
    count = await character_service.batch_delete(ids)
    return BaseResponse(success=True, message=f"Deleted {count} characters")


@admin_api_router.get("/characters")
async def list_characters_api(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    search: str = "",
    top_category: str = "",
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_service import character_service
    
    characters, total = await character_service.list_characters(
        page=page,
        page_size=page_size,
        top_category=top_category if top_category else None,
        is_official=True,
        search=search if search else None,
        order_by="created_at DESC",
    )
    
    return {
        "items": characters,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_api_router.post("/characters")
async def create_character_api(
    request: Request,
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    generate_images = data.pop("generate_images", False)
    generate_video = data.pop("generate_video", False)

    if generate_images:
        from app.services.character_factory import character_factory
        from app.models.character import CharacterCreate

        # Build a base character first so factory has a profile dict to work with
        from app.services.character_service import character_service
        character_create = CharacterCreate(**data)
        character = await character_service.create_character(character_create)

        character_id = character.get("id")
        if character_id:
            images = await character_factory._generate_character_images(character)
            if images:
                from app.models.character import CharacterUpdate
                update = CharacterUpdate(**images)
                character = await character_service.update_character(character_id, update) or character

            if generate_video:
                import asyncio
                video_source = images.get("mature_image_url") or images.get("avatar_url")
                if video_source:
                    asyncio.create_task(
                        character_factory._generate_and_save_video(character_id, character, video_source)
                    )

        return character

    from app.services.character_service import character_service
    from app.models.character import CharacterCreate

    character_create = CharacterCreate(**data)
    return await character_service.create_character(character_create)


@admin_api_router.get("/characters/pending-review")
async def list_pending_characters(
    request: Request,
    page: int = 1,
    page_size: int = 20,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_service import character_service
    
    characters, total = await character_service.list_pending_characters(
        page=page,
        page_size=page_size,
    )
    
    return {
        "items": characters,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@admin_api_router.get("/characters/{character_id}")
async def get_character_api(
    request: Request,
    character_id: str,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_service import character_service
    
    character = await character_service.get_character_by_id(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return character


@admin_api_router.put("/characters/{character_id}")
async def update_character_api(
    request: Request,
    character_id: str,
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_service import character_service
    from app.models.character import CharacterUpdate
    
    update_data = CharacterUpdate(**data)
    character = await character_service.update_character(character_id, update_data)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return character


@admin_api_router.post("/characters/{character_id}/regenerate-mature")
async def regenerate_mature_media_api(
    request: Request,
    character_id: str,
    admin: User = Depends(get_admin_user),
    generate_video: bool = False,
) -> dict[str, Any]:
    from app.services.character_factory import character_factory

    try:
        character = await character_factory.regenerate_mature_media(
            character_id, generate_video=generate_video
        )
        return {"success": True, "character": character}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mature generation failed: {e}")


@admin_api_router.delete("/characters/{character_id}", response_model=BaseResponse)
async def delete_character_api(
    request: Request,
    character_id: str,
    admin: User = Depends(get_admin_user)
) -> BaseResponse:
    from app.services.character_service import character_service
    
    success = await character_service.delete_character(character_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return BaseResponse(success=True, message="Character deleted")


@admin_api_router.post("/characters/batch-generate")
async def batch_generate_characters_api(
    request: Request,
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_factory import character_factory
    from app.models.character import CharacterBatchGenerate
    
    config = CharacterBatchGenerate(**data)
    
    characters = await character_factory.generate_batch(
        count=config.count,
        top_category=config.top_category,
        ethnicity=config.ethnicity,
        nationality=config.nationality,
        occupation=config.occupation,
        personality_preferences=config.personality_preferences,
        age_min=config.age_min or 20,
        age_max=config.age_max or 30,
        generate_images=config.generate_images,
        generate_video=config.generate_video,
        optimize_seo=config.optimize_seo,
    )
    
    return {
        "success": True,
        "created_count": len(characters),
        "characters": characters,
    }


@admin_api_router.post("/characters/from-template")
async def generate_from_template_api(
    request: Request,
    config: CharacterFromTemplate,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_factory import character_factory
    
    try:
        characters = await character_factory.generate_from_template(
            template_id=config.template_id,
            variations=config.variations,
            ethnicity=config.ethnicity,
            nationality=config.nationality,
            generate_images=config.generate_images,
            generate_video=config.generate_video,
            optimize_seo=config.optimize_seo,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "success": True,
        "created_count": len(characters),
        "characters": characters,
    }


@admin_api_router.post("/characters/{character_id}/regenerate-images")
async def regenerate_character_images_api(
    request: Request,
    character_id: str,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_factory import character_factory
    
    try:
        character = await character_factory.regenerate_images(character_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    return character


@admin_api_router.post("/characters/{character_id}/regenerate-video")
async def regenerate_character_video_api(
    request: Request,
    character_id: str,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_factory import character_factory
    
    try:
        character = await character_factory.regenerate_video(character_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return character


@admin_api_router.get("/character-templates")
async def list_character_templates_api(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    from app.models.character import OCCUPATION_TEMPLATES, ETHNICITY_IMAGE_STYLES, NATIONALITY_CONFIGS
    
    templates = [
        {
            "id": template_id,
            "name": template_data.get("name", template_id),
            "description": template_data.get("description", ""),
            "age_range": template_data.get("age_range", (20, 30)),
            "personality_pool": template_data.get("personality_pool", []),
        }
        for template_id, template_data in OCCUPATION_TEMPLATES.items()
    ]
    
    return templates


@admin_api_router.get("/ethnicity-options")
async def list_ethnicity_options(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    from app.models.character import ETHNICITY_IMAGE_STYLES
    
    return [
        {"id": ethnicity_id, "name": ethnicity_id.replace("_", " ").title()}
        for ethnicity_id in ETHNICITY_IMAGE_STYLES.keys()
    ]


@admin_api_router.get("/nationality-options")
async def list_nationality_options(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    from app.models.character import NATIONALITY_CONFIGS
    
    return [
        {
            "id": nationality_id, 
            "name": nationality_id.upper(),
            "name_pool": config.get("name_pool", [])[:5],
            "cultural_traits": config.get("cultural_traits", []),
        }
        for nationality_id, config in NATIONALITY_CONFIGS.items()
    ]


@admin_api_router.get("/trends")
async def list_trends_api(
    request: Request,
    limit: int = 50,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    from app.services.trend_service import trend_service
    return await trend_service.get_stored_trends(limit=limit)


@admin_api_router.post("/trends/refresh")
async def refresh_trends_api(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.trend_service import trend_service
    return await trend_service.refresh_trends()


@admin_api_router.get("/trends/attributes")
async def get_trend_attributes_api(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.trend_service import trend_service
    return await trend_service.get_trend_weighted_attributes()


@admin_api_router.post("/characters/trend-generate")
async def trend_generate_characters_api(
    request: Request,
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_factory import character_factory
    
    count = data.get("count", 1)
    top_category = data.get("top_category", "girls")
    generate_images = data.get("generate_images", True)
    generate_video = data.get("generate_video", False)
    optimize_seo = data.get("optimize_seo", True)
    
    characters = await character_factory.generate_batch_trend_aware(
        count=count,
        top_category=top_category,
        generate_images=generate_images,
        generate_video=generate_video,
        optimize_seo=optimize_seo,
    )
    
    return {
        "success": True,
        "created_count": len(characters),
        "characters": characters,
    }


@admin_api_router.get("/performance/weights")
async def get_performance_weights_api(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.performance_analyzer import performance_analyzer
    return await performance_analyzer.analyze_top_performers(days=30)


@admin_api_router.post("/performance/analyze")
async def analyze_performance_api(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.performance_analyzer import performance_analyzer
    analysis = await performance_analyzer.analyze_top_performers(days=30)
    updated = await performance_analyzer.update_generation_weights(analysis)
    return {"success": True, "weights_updated": updated}


@admin_api_router.post("/scheduler/run-job")
async def run_scheduler_job_api(
    request: Request,
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    job_id = data.get("job_id")
    if not job_id:
        return {"success": False, "message": "job_id is required"}
    
    job_functions = {
        "fetch_google_trends": "app.services.scheduler_service.fetch_google_trends",
        "rebuild_user_preference_profiles": "app.services.scheduler_service.rebuild_user_preference_profiles",
        "analyze_character_performance": "app.services.scheduler_service.analyze_character_performance",
        "record_daily_performance": "app.services.scheduler_service.record_daily_performance",
        "check_subscription_expiry": "app.services.scheduler_service.check_subscription_expiry",
        "grant_monthly_credits": "app.services.scheduler_service.grant_monthly_credits_job",
    }
    
    if job_id not in job_functions:
        available = list(job_functions.keys())
        return {"success": False, "message": f"Unknown job_id. Available: {available}"}
    
    import importlib
    module_path, func_name = job_functions[job_id].rsplit(".", 1)
    module = importlib.import_module(module_path)
    func = getattr(module, func_name)
    
    try:
        await func()
        return {"success": True, "message": f"Job {job_id} executed successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@admin_api_router.get("/scheduler/jobs")
async def list_scheduler_jobs_api(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    return [
        {"id": "fetch_google_trends", "name": "Fetch Google Trends", "schedule": "Daily at 03:00"},
        {"id": "rebuild_user_preference_profiles", "name": "Rebuild User Preferences", "schedule": "Daily at 05:00"},
        {"id": "analyze_character_performance", "name": "Analyze Performance", "schedule": "Daily at 04:00"},
        {"id": "record_daily_performance", "name": "Record Daily Performance", "schedule": "Daily at 01:00"},
        {"id": "check_subscription_expiry", "name": "Check Subscription Expiry", "schedule": "Every 6 hours"},
        {"id": "grant_monthly_credits", "name": "Grant Monthly Credits", "schedule": "Daily at 02:00"},
    ]


@router.get("/stories")
async def list_stories_admin(
    request: Request,
    search: str = "",
    status: str = "",
    emotion_tone: str = "",
    relation_type: str = "",
    character_gender: str = "",
    era: str = "",
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    from app.core.database import db
    
    offset = (page - 1) * page_size
    conditions = []
    params = []
    
    if search:
        conditions.append("(title LIKE ? OR title_en LIKE ? OR summary LIKE ?)")
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    
    if status:
        conditions.append("status = ?")
        params.append(status)
    
    if emotion_tone:
        conditions.append("emotion_tones LIKE ?")
        params.append(f"%{emotion_tone}%")
    
    if relation_type:
        conditions.append("relation_types LIKE ?")
        params.append(f"%{relation_type}%")
    
    if character_gender:
        conditions.append("character_gender = ?")
        params.append(character_gender)
    
    if era:
        conditions.append("era = ?")
        params.append(era)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    count_query = f"SELECT COUNT(*) as count FROM script_library WHERE {where_clause}"
    count_result = await db.execute(count_query, tuple(params), fetch=True)
    total = count_result["count"] if count_result else 0
    
    data_query = f"""
        SELECT id, title, title_en, summary, emotion_tones, relation_types,
               character_gender, era, profession, status, popularity, created_at, updated_at
        FROM script_library 
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([page_size, offset])
    rows = await db.execute(data_query, tuple(params), fetch_all=True)
    
    stories = []
    for row in rows or []:
        stories.append({
            "id": row.get("id"),
            "title": row.get("title"),
            "title_en": row.get("title_en"),
            "summary": row.get("summary"),
            "emotion_tones": row.get("emotion_tones"),
            "relation_types": row.get("relation_types"),
            "character_gender": row.get("character_gender"),
            "era": row.get("era"),
            "profession": row.get("profession"),
            "status": row.get("status"),
            "popularity": row.get("popularity", 0),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        })
    
    return {
        "stories": stories,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/stories/create")
async def create_story_page(request: Request) -> dict[str, Any]:
    return {"page": "create_story"}


@router.post("/stories/ai-generate", response_model=Task)
async def ai_generate_story(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_story_gen",
        type="story_generation",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/stories/create", response_model=BaseResponse)
async def create_story_admin(request: Request, data: dict[str, Any]) -> BaseResponse:
    from app.core.database import db
    
    story_id = data.get("id") or f"manual_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    now = datetime.now().isoformat()
    
    await db.execute(
        """INSERT INTO script_library 
           (id, title, title_en, summary, emotion_tones, relation_types, 
            contrast_types, era, gender_target, character_gender, profession,
            length, age_rating, contrast_surface, contrast_truth, contrast_hook,
            script_seed, full_script, status, popularity, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            story_id,
            data.get("title", ""),
            data.get("title_en", ""),
            data.get("summary", ""),
            data.get("emotion_tones", "[]"),
            data.get("relation_types", "[]"),
            data.get("contrast_types", "[]"),
            data.get("era", "modern_urban"),
            data.get("gender_target", "male"),
            data.get("character_gender", "female_char"),
            data.get("profession", ""),
            data.get("length", "medium"),
            data.get("age_rating", "all"),
            data.get("contrast_surface", ""),
            data.get("contrast_truth", ""),
            data.get("contrast_hook", ""),
            data.get("script_seed", "{}"),
            data.get("full_script", ""),
            data.get("status", "draft"),
            data.get("popularity", 0),
            now,
            now
        )
    )
    
    return BaseResponse(success=True, message="Story created")


@router.get("/stories/{story_id}/edit")
async def edit_story_page(request: Request, story_id: str) -> dict[str, Any]:
    from app.core.database import db
    
    row = await db.execute(
        "SELECT * FROM script_library WHERE id = ?",
        (story_id,),
        fetch=True
    )
    
    if not row:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return {"story": dict(row)}


@router.post("/stories/{story_id}/update", response_model=BaseResponse)
async def update_story_admin(
    request: Request, 
    story_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    from app.core.database import db
    
    now = datetime.now().isoformat()
    
    await db.execute(
        """UPDATE script_library SET
           title = ?, title_en = ?, summary = ?, emotion_tones = ?, relation_types = ?,
           contrast_types = ?, era = ?, gender_target = ?, character_gender = ?, profession = ?,
           length = ?, age_rating = ?, contrast_surface = ?, contrast_truth = ?, contrast_hook = ?,
           script_seed = ?, full_script = ?, status = ?, popularity = ?, updated_at = ?
           WHERE id = ?""",
        (
            data.get("title", ""),
            data.get("title_en", ""),
            data.get("summary", ""),
            data.get("emotion_tones", "[]"),
            data.get("relation_types", "[]"),
            data.get("contrast_types", "[]"),
            data.get("era", "modern_urban"),
            data.get("gender_target", "male"),
            data.get("character_gender", "female_char"),
            data.get("profession", ""),
            data.get("length", "medium"),
            data.get("age_rating", "all"),
            data.get("contrast_surface", ""),
            data.get("contrast_truth", ""),
            data.get("contrast_hook", ""),
            data.get("script_seed", "{}"),
            data.get("full_script", ""),
            data.get("status", "draft"),
            data.get("popularity", 0),
            now,
            story_id
        )
    )
    
    return BaseResponse(success=True, message="Story updated")


@router.post("/stories/{story_id}/update-json", response_model=BaseResponse)
async def update_story_json(
    request: Request, 
    story_id: str, 
    data: dict[str, Any]
) -> BaseResponse:
    return BaseResponse(success=True, message="Story JSON updated")


@router.post("/stories/{story_id}/delete", response_model=BaseResponse)
async def delete_story_admin(request: Request, story_id: str) -> BaseResponse:
    from app.core.database import db
    
    result = await db.execute(
        "DELETE FROM script_library WHERE id = ?",
        (story_id,)
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return BaseResponse(success=True, message="Story deleted")


@admin_api_router.post("/stories/batch-delete", response_model=BaseResponse)
async def batch_delete_stories(request: Request, data: dict[str, Any]) -> BaseResponse:
    from app.core.database import db
    
    ids = data.get("ids", [])
    if not ids:
        return BaseResponse(success=False, message="No IDs provided")
    
    placeholders = ",".join("?" * len(ids))
    await db.execute(
        f"DELETE FROM script_library WHERE id IN ({placeholders})",
        tuple(ids)
    )
    
    return BaseResponse(success=True, message=f"Deleted {len(ids)} stories")


@router.get("/tags", response_model=dict)
async def list_tags_admin(
    request: Request,
    category: str = "",
    page: int = 1,
    page_size: int = 200,
) -> dict[str, Any]:
    from app.core.database import db
    
    conditions = []
    params = []
    
    if category:
        conditions.append("category = ?")
        params.append(category)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    count_result = await db.execute(
        f"SELECT COUNT(*) as count FROM script_tags WHERE {where_clause}",
        tuple(params),
        fetch=True
    )
    total = count_result["count"] if count_result else 0
    
    offset = (page - 1) * page_size
    rows = await db.execute(
        f"SELECT * FROM script_tags WHERE {where_clause} ORDER BY category, name LIMIT ? OFFSET ?",
        tuple(params) + (page_size, offset),
        fetch_all=True
    )
    
    return {
        "tags": [dict(r) for r in (rows or [])],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/tags", response_model=BaseResponse)
async def create_tag_admin(request: Request, data: dict[str, Any]) -> BaseResponse:
    from app.core.database import db
    
    tag_id = data.get("id", "").strip()
    category = data.get("category", "").strip()
    name = data.get("name", "").strip()
    
    if not tag_id or not category or not name:
        raise HTTPException(status_code=400, detail="id, category, name are required")
    
    existing = await db.execute(
        "SELECT id FROM script_tags WHERE id = ?",
        (tag_id,),
        fetch=True
    )
    if existing:
        raise HTTPException(status_code=409, detail="Tag ID already exists")
    
    import json
    now = datetime.now().isoformat()
    await db.execute(
        """INSERT INTO script_tags (id, category, name, name_en, description, examples, parent_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            tag_id,
            category,
            name,
            data.get("name_en", ""),
            data.get("description", ""),
            json.dumps(data.get("examples", [])),
            data.get("parent_id"),
        )
    )
    
    return BaseResponse(success=True, message="Tag created")


@router.put("/tags/{tag_id}", response_model=BaseResponse)
async def update_tag_admin(
    request: Request,
    tag_id: str,
    data: dict[str, Any]
) -> BaseResponse:
    from app.core.database import db
    
    existing = await db.execute(
        "SELECT id FROM script_tags WHERE id = ?",
        (tag_id,),
        fetch=True
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    import json
    sets = []
    params = []
    
    for field in ["category", "name", "name_en", "description", "parent_id"]:
        if field in data:
            sets.append(f"{field} = ?")
            params.append(data[field])
    
    if "examples" in data:
        sets.append("examples = ?")
        params.append(json.dumps(data["examples"]))
    
    if not sets:
        return BaseResponse(success=True, message="No changes")
    
    params.append(tag_id)
    await db.execute(
        f"UPDATE script_tags SET {', '.join(sets)} WHERE id = ?",
        tuple(params)
    )
    
    return BaseResponse(success=True, message="Tag updated")


@router.delete("/tags/{tag_id}", response_model=BaseResponse)
async def delete_tag_admin(request: Request, tag_id: str) -> BaseResponse:
    from app.core.database import db
    
    existing = await db.execute(
        "SELECT id FROM script_tags WHERE id = ?",
        (tag_id,),
        fetch=True
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    await db.execute("DELETE FROM script_tag_relations WHERE tag_id = ?", (tag_id,))
    await db.execute("DELETE FROM script_tags WHERE id = ?", (tag_id,))
    
    return BaseResponse(success=True, message="Tag deleted")


@router.post("/tags/batch", response_model=BaseResponse)
async def batch_create_tags_admin(request: Request, data: dict[str, Any]) -> BaseResponse:
    from app.core.database import db
    
    tags = data.get("tags", [])
    if not tags:
        raise HTTPException(status_code=400, detail="No tags provided")
    
    import json
    created = 0
    for tag in tags:
        tag_id = tag.get("id", "").strip()
        if not tag_id:
            continue
        
        existing = await db.execute(
            "SELECT id FROM script_tags WHERE id = ?",
            (tag_id,),
            fetch=True
        )
        if existing:
            await db.execute(
                """UPDATE script_tags SET category = ?, name = ?, name_en = ?, description = ?, examples = ?, parent_id = ?
                   WHERE id = ?""",
                (
                    tag.get("category", ""),
                    tag.get("name", ""),
                    tag.get("name_en", ""),
                    tag.get("description", ""),
                    json.dumps(tag.get("examples", [])),
                    tag.get("parent_id"),
                    tag_id,
                )
            )
        else:
            await db.execute(
                """INSERT INTO script_tags (id, category, name, name_en, description, examples, parent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    tag_id,
                    tag.get("category", ""),
                    tag.get("name", ""),
                    tag.get("name_en", ""),
                    tag.get("description", ""),
                    json.dumps(tag.get("examples", [])),
                    tag.get("parent_id"),
                )
            )
            created += 1
    
    return BaseResponse(success=True, message=f"Created {created} tags, updated {len(tags) - created} tags")


@admin_api_router.post("/characters/{character_id}/approve")
async def approve_character(
    request: Request,
    character_id: str,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_service import character_service
    
    character = await character_service.approve_character(character_id, admin.id)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return character


@admin_api_router.post("/characters/{character_id}/reject")
async def reject_character(
    request: Request,
    character_id: str,
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.character_service import character_service
    
    reason = data.get("rejection_reason")
    
    character = await character_service.reject_character(character_id, admin.id, reason)
    
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    
    return character


@router.get("/batch-generate")
async def batch_generate_page(request: Request) -> dict[str, Any]:
    return {"page": "batch_generate"}


@router.get("/batch-jobs")
async def list_batch_jobs(request: Request) -> dict[str, Any]:
    return {
        "jobs": [
            {"id": "job_001", "status": "completed", "created_at": datetime.now().isoformat()}
        ]
    }


@admin_api_router.get("/batch-variables")
async def get_batch_variables(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    return [{"name": "variable1", "type": "string"}]


@admin_api_router.post("/batch-generate", response_model=Task)
async def start_batch_generate(
    request: Request, 
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> Task:
    return Task(
        id="task_batch_gen",
        type="batch_generation",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@admin_api_router.get("/batch-jobs/{batch_job_id}")
async def get_batch_job(
    request: Request, 
    batch_job_id: str,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    return {
        "id": batch_job_id,
        "status": "completed",
        "progress": 100,
        "created_at": datetime.now().isoformat(),
    }


@router.get("/seo-generate")
async def seo_generate_page(request: Request) -> dict[str, Any]:
    return {"page": "seo_generate"}


@admin_api_router.post("/seo-generate", response_model=Task)
async def start_seo_generate(
    request: Request, 
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> Task:
    return Task(
        id="task_seo_gen",
        type="seo_generation",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@admin_api_router.post("/seo-keywords/import-csv", response_model=BaseResponse)
async def import_seo_keywords(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> BaseResponse:
    return BaseResponse(success=True, message="SEO keywords imported")


@router.get("/seo-keywords")
async def list_seo_keywords(request: Request) -> dict[str, Any]:
    return {
        "keywords": [
            {"keyword": "AI chat", "volume": 1000, "difficulty": 50}
        ]
    }


@router.get("/scripts")
async def scripts_page(request: Request) -> dict[str, Any]:
    return {"page": "scripts"}


@router.get("/scripts/workshop")
async def scripts_workshop(request: Request) -> dict[str, Any]:
    return {"page": "scripts_workshop"}


@router.post("/scripts/generate-preview", response_model=Task)
async def generate_script_preview(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_script_preview",
        type="script_preview",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/scripts/create-template", response_model=BaseResponse)
async def create_script_template(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Script template created")


@router.post("/scripts/delete-template/{template_id}", response_model=BaseResponse)
async def delete_script_template(request: Request, template_id: str) -> BaseResponse:
    return BaseResponse(success=True, message="Script template deleted")


@router.post("/scripts/extract-novel", response_model=Task)
async def extract_novel(request: Request, data: dict[str, Any]) -> Task:
    return Task(
        id="task_extract_novel",
        type="novel_extraction",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.get("/scripts/gutenberg/fetch")
async def gutenberg_fetch(request: Request) -> dict[str, Any]:
    return {"books": [{"id": 1, "title": "Sample Book"}]}


@router.get("/scripts/seo-trending")
async def seo_trending(request: Request) -> dict[str, Any]:
    return {"trending": ["AI chat", "virtual companion", "chatbot"]}


@router.post("/scripts/refresh-seo-trends", response_model=BaseResponse)
async def refresh_seo_trends(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="SEO trends refreshed")


@router.post("/scripts/publish", response_model=BaseResponse)
async def publish_script(request: Request, data: dict[str, Any]) -> BaseResponse:
    return BaseResponse(success=True, message="Script published")


@router.get("/dashboard")
async def admin_dashboard(request: Request) -> dict[str, Any]:
    from app.core.database import db
    
    total_users = await db.execute("SELECT COUNT(*) FROM users", fetch=True)
    total_characters = await db.execute("SELECT COUNT(*) FROM characters", fetch=True)
    total_stories = await db.execute("SELECT COUNT(*) FROM scripts", fetch=True)
    total_chats = await db.execute("SELECT COUNT(*) FROM chat_sessions", fetch=True)
    total_messages = await db.execute("SELECT COUNT(*) FROM chat_messages", fetch=True)
    
    return {
        "stats": {
            "total_users": total_users["COUNT(*)"] if total_users else 0,
            "total_characters": total_characters["COUNT(*)"] if total_characters else 0,
            "total_stories": total_stories["COUNT(*)"] if total_stories else 0,
            "total_chats": total_chats["COUNT(*)"] if total_chats else 0,
            "total_messages": total_messages["COUNT(*)"] if total_messages else 0,
        }
    }


@router.get("/tasks")
async def list_admin_tasks(request: Request) -> dict[str, Any]:
    return {
        "tasks": [
            {"id": "task_001", "type": "generation", "status": "pending"}
        ]
    }


@router.get("/characters/quick-create")
async def quick_create_page(request: Request) -> dict[str, Any]:
    return {"page": "quick_create"}


@router.get("/characters/create")
async def create_character_page(request: Request) -> dict[str, Any]:
    return {"page": "create_character"}


@router.get("/characters/quick-create/status/{task_id}", response_model=Task)
async def quick_create_status(request: Request, task_id: str) -> Task:
    return Task(
        id=task_id,
        type="quick_create",
        status=TaskStatus.COMPLETED,
        created_at=datetime.now(),
    )


@router.get("/voices")
async def voices_page(request: Request) -> dict[str, Any]:
    return {"page": "voices"}


@admin_api_router.get("/voices")
async def list_voices(
    request: Request,
    provider: Optional[str] = None,
    language: Optional[str] = None,
    gender: Optional[str] = None,
    tone: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 50,
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.voice_management_service import voice_management_service
    return await voice_management_service.list_voices(
        provider=provider,
        language=language,
        gender=gender,
        tone=tone,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )


@admin_api_router.post("/voices")
async def create_voice(
    request: Request,
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.voice_management_service import voice_management_service
    data = await request.json()
    return await voice_management_service.create_voice(data)


@admin_api_router.patch("/voices/{voice_id}")
async def update_voice(
    request: Request,
    voice_id: str,
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.voice_management_service import voice_management_service
    data = await request.json()
    voice = await voice_management_service.update_voice(voice_id, data)
    if not voice:
        raise HTTPException(status_code=404, detail="Voice not found")
    return voice


@admin_api_router.delete("/voices/{voice_id}")
async def delete_voice(
    request: Request,
    voice_id: str,
    admin: User = Depends(get_admin_user),
) -> BaseResponse:
    from app.services.voice_management_service import voice_management_service
    success = await voice_management_service.delete_voice(voice_id)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot delete voice. It may be in use by characters.")
    return BaseResponse(success=True, message="Voice deleted")


@admin_api_router.post("/voices/{voice_id}/preview")
async def generate_voice_preview(
    request: Request,
    voice_id: str,
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.voice_management_service import voice_management_service
    data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    try:
        result = await voice_management_service.generate_preview(voice_id, text=data.get("text"))
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")


@admin_api_router.post("/voices/sync/elevenlabs")
async def sync_elevenlabs(
    request: Request,
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.voice_management_service import voice_management_service
    return await voice_management_service.sync_from_elevenlabs()


@admin_api_router.post("/voices/sync/dashscope")
async def sync_dashscope(
    request: Request,
    admin: User = Depends(get_admin_user),
) -> dict[str, Any]:
    from app.services.voice_management_service import voice_management_service
    return await voice_management_service.sync_from_dashscope()


@router.post("/characters/{character_id}/regenerate-voice", response_model=Task)
async def regenerate_voice(request: Request, character_id: str) -> Task:
    return Task(
        id="task_voice_regenerate",
        type="voice_regeneration",
        status=TaskStatus.PENDING,
        created_at=datetime.now(),
    )


@router.post("/characters/{character_id}/preview-voice")
async def preview_voice(request: Request, character_id: str) -> dict[str, Any]:
    return {
        "audio_url": "https://example.com/preview.mp3",
        "duration": 5,
    }


@router.post("/upload-voice-to-r2", response_model=BaseResponse)
async def upload_voice_to_r2(request: Request) -> BaseResponse:
    return BaseResponse(success=True, message="Voice uploaded to R2")


@router.get("/prompts/new")
async def new_prompt_page(request: Request) -> dict[str, Any]:
    return {"page": "new_prompt"}


@router.get("/settings")
async def settings_page(request: Request) -> dict[str, Any]:
    return {"page": "settings"}


@router.get("/api/users")
async def list_users_api(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    return [
        {
            "id": "user_001",
            "email": "user@example.com",
            "display_name": "Test User",
            "is_admin": False,
            "is_banned": False,
            "subscription_tier": "premium",
            "created_at": datetime.now().isoformat(),
        }
    ]


@router.post("/api/users/{user_id}/ban", response_model=BaseResponse)
async def ban_user(
    request: Request, 
    user_id: str,
    admin: User = Depends(get_admin_user)
) -> BaseResponse:
    return BaseResponse(success=True, message="User banned")


@router.post("/api/users/{user_id}/unban", response_model=BaseResponse)
async def unban_user(
    request: Request, 
    user_id: str,
    admin: User = Depends(get_admin_user)
) -> BaseResponse:
    return BaseResponse(success=True, message="User unbanned")


@router.get("/api/orders")
async def list_orders_api(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    return [
        {
            "id": "order_001",
            "user_id": "user_001",
            "user_email": "user@example.com",
            "amount": 9.99,
            "currency": "USD",
            "status": "completed",
            "payment_method": "ccbill",
            "created_at": datetime.now().isoformat(),
        }
    ]


config_router = APIRouter(prefix="/api/admin/api/config", tags=["admin-config"])

SENSITIVE_CONFIG_KEYS = frozenset([
    "LLM_API_KEY", "STRIPE_SECRET_KEY", "JWT_SECRET", "JWT_SECRET_KEY",
    "R2_SECRET_ACCESS_KEY", "SMTP_PASSWORD", "ADMIN_PASSWORD",
    "NOVITA_API_KEY", "ELEVENLABS_API_KEY",
    "SORA_API_KEY", "RECAPTCHA_SECRET_KEY", "LIVEKIT_API_SECRET",
    "CCBILL_CLIENT_SECRET", "STRIPE_WEBHOOK_SECRET",
    "CF_API_TOKEN", "OPENAI_API_KEY",
    "USDT_PAYMENT_GATEWAY_API_KEY", "TELEGRAM_STAR_GATEWAY_API_TOKEN",
    "TELEGRAM_BOT_TOKEN",
])


def _redact_sensitive_config(config_dict: dict[str, Any]) -> dict[str, Any]:
    for key in SENSITIVE_CONFIG_KEYS:
        if key in config_dict:
            config_dict[key] = "***REDACTED***"
    return config_dict


@config_router.get("")
async def get_all_configs(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.config_service import ConfigService
    from app.models.config import ConfigGroup
    
    config_service = ConfigService()
    configs = await config_service.get_all_configs()
    
    for group in configs.values():
        if "values" in group:
            group["values"] = _redact_sensitive_config(group["values"])
    
    return {
        "groups": [config for config in configs.values()]
    }


@config_router.get("/groups")
async def get_config_groups(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> list[dict[str, Any]]:
    from app.services.config_service import ConfigService
    
    config_service = ConfigService()
    return config_service.get_group_definitions()


@config_router.get("/{group}")
async def get_config_by_group(
    request: Request, 
    group: str,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.config_service import ConfigService
    from app.models.config import ConfigGroup
    
    config_service = ConfigService()
    try:
        config_group = ConfigGroup(group)
        result = await config_service.get_config_by_group(config_group)
        if "values" in result:
            result["values"] = _redact_sensitive_config(result["values"])
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid config group: {group}")


@config_router.put("/{group}")
async def update_config_group(
    request: Request, 
    group: str,
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.config_service import ConfigService
    from app.models.config import ConfigGroup
    from app.core.config import clear_config_cache
    
    config_service = ConfigService()
    try:
        config_group = ConfigGroup(group)
        values = data.get("values", {})
        result = await config_service.update_config_group(config_group, values)
        clear_config_cache()
        from app.services.llm_service import LLMService
        from app.services.media_service import MediaService
        llm_instance = LLMService.get_instance()
        media_instance = MediaService.get_instance()
        await llm_instance.refresh_providers()
        await media_instance.refresh_providers()
        return {
            "success": True,
            "message": f"Updated {result['count']} configuration(s)",
            "updated": result["updated"],
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid config group: {group}")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@config_router.post("/init-defaults")
async def init_config_defaults(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.config_service import ConfigService

    config_service = ConfigService()
    count = await config_service.init_defaults()
    return {
        "success": True,
        "message": f"Initialized {count} default configuration(s)",
        "count": count,
    }


@config_router.post("/test/email")
async def test_email_config(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    """Send a test email using current SMTP configuration."""
    import smtplib
    import ssl
    from email.mime.text import MIMEText
    from app.core.config import get_smtp_config

    cfg = await get_smtp_config()
    if not cfg.get("host") or not cfg.get("username"):
        raise HTTPException(status_code=400, detail="SMTP 未配置 (Host 和 Username 必填)")

    msg = MIMEText("这是来自 Roxy 管理员设置的测试邮件。\n\nThis is a test email from Roxy Admin Settings.")
    msg["Subject"] = "Roxy SMTP 测试 - Test Email"
    msg["From"] = cfg.get("from_email") or cfg["username"]
    msg["To"] = admin.email

    try:
        if cfg["use_ssl"]:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(cfg["host"], cfg["ssl_port"], context=ctx) as s:
                s.login(cfg["username"], cfg["password"])
                s.send_message(msg)
        else:
            with smtplib.SMTP(cfg["host"], cfg["starttls_port"]) as s:
                if cfg["use_starttls"]:
                    s.starttls()
                s.login(cfg["username"], cfg["password"])
                s.send_message(msg)
        return {"success": True, "message": f"测试邮件已发送到 {admin.email}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMTP 错误: {str(e)}")


@config_router.get("/models/{provider}")
async def get_available_models(
    request: Request,
    provider: str,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from pathlib import Path
    
    models_data = []
    
    if provider == "novita":
        models_data = [
            {"id": "zai-org/glm-4.7-flash", "display_name": "GLM-4.7-Flash", "context_size": 200000},
            {"id": "deepseek/deepseek-v3.2", "display_name": "Deepseek V3.2", "context_size": 163840},
            {"id": "zai-org/glm-5.1", "display_name": "GLM-5.1", "context_size": 204800},
            {"id": "google/gemma-4-26b-a4b-it", "display_name": "Gemma 4 26B A4B", "context_size": 262144},
            {"id": "google/gemma-4-31b-it", "display_name": "Gemma 4 31B", "context_size": 262144},
            {"id": "minimax/minimax-m2.7", "display_name": "MiniMax M2.7", "context_size": 204800},
            {"id": "minimax/minimax-m2.5-highspeed", "display_name": "MiniMax M2.5-highspeed", "context_size": 204800},
            {"id": "qwen/qwen3.5-27b", "display_name": "Qwen3.5-27B", "context_size": 262144},
            {"id": "qwen/qwen3.5-122b-a10b", "display_name": "Qwen3.5-122B-A10B", "context_size": 262144},
            {"id": "qwen/qwen3.5-35b-a3b", "display_name": "Qwen3.5-35B-A3B", "context_size": 262144},
            {"id": "qwen/qwen3.5-397b-a17b", "display_name": "Qwen3.5-397B-A17B", "context_size": 262144},
            {"id": "minimax/minimax-m2.5", "display_name": "MiniMax M2.5", "context_size": 204800},
            {"id": "zai-org/glm-5", "display_name": "GLM-5", "context_size": 202800},
            {"id": "qwen/qwen3-coder-next", "display_name": "Qwen3 Coder Next", "context_size": 262144},
            {"id": "deepseek/deepseek-ocr-2", "display_name": "DeepSeek-OCR 2", "context_size": 8192},
            {"id": "moonshotai/kimi-k2.5", "display_name": "Kimi K2.5", "context_size": 262144},
            {"id": "minimax/minimax-m2.1", "display_name": "Minimax M2.1", "context_size": 204800},
            {"id": "zai-org/glm-4.7", "display_name": "GLM-4.7", "context_size": 204800},
            {"id": "xiaomimimo/mimo-v2-flash", "display_name": "XiaomiMiMo/MiMo-V2-Flash", "context_size": 262144},
            {"id": "zai-org/autoglm-phone-9b-multilingual", "display_name": "AutoGLM-Phone-9B-Multilingual", "context_size": 65536},
            {"id": "moonshotai/kimi-k2-thinking", "display_name": "Kimi K2 Thinking", "context_size": 262144},
            {"id": "minimax/minimax-m2", "display_name": "MiniMax-M2", "context_size": 204800},
            {"id": "paddlepaddle/paddleocr-vl", "display_name": "PaddleOCR-VL", "context_size": 16384},
            {"id": "deepseek/deepseek-v3.2-exp", "display_name": "Deepseek V3.2 Exp", "context_size": 163840},
            {"id": "qwen/qwen3-vl-235b-a22b-thinking", "display_name": "Qwen3 VL 235B A22B Thinking", "context_size": 131072},
            {"id": "zai-org/glm-4.6v", "display_name": "GLM 4.6V", "context_size": 131072},
            {"id": "zai-org/glm-4.6", "display_name": "GLM 4.6", "context_size": 204800},
            {"id": "kwaipilot/kat-coder-pro", "display_name": "Kat Coder Pro", "context_size": 256000},
            {"id": "qwen/qwen3-next-80b-a3b-instruct", "display_name": "Qwen3 Next 80B A3B Instruct", "context_size": 131072},
            {"id": "qwen/qwen3-next-80b-a3b-thinking", "display_name": "Qwen3 Next 80B A3B Thinking", "context_size": 131072},
            {"id": "deepseek/deepseek-ocr", "display_name": "DeepSeek-OCR", "context_size": 8192},
            {"id": "deepseek/deepseek-v3.1-terminus", "display_name": "Deepseek V3.1 Terminus", "context_size": 131072},
            {"id": "qwen/qwen3-vl-235b-a22b-instruct", "display_name": "Qwen3 VL 235B A22B Instruct", "context_size": 131072},
            {"id": "qwen/qwen3-max", "display_name": "Qwen3 Max", "context_size": 262144},
            {"id": "deepseek/deepseek-v3.1", "display_name": "DeepSeek V3.1", "context_size": 131072},
            {"id": "moonshotai/kimi-k2-0905", "display_name": "Kimi K2 0905", "context_size": 262144},
            {"id": "qwen/qwen3-coder-480b-a35b-instruct", "display_name": "Qwen3 Coder 480B A35B Instruct", "context_size": 262144},
            {"id": "qwen/qwen3-coder-30b-a3b-instruct", "display_name": "Qwen3 Coder 30b A3B Instruct", "context_size": 160000},
            {"id": "openai/gpt-oss-120b", "display_name": "OpenAI GPT OSS 120B", "context_size": 131072},
            {"id": "moonshotai/kimi-k2-instruct", "display_name": "Kimi K2 Instruct", "context_size": 131072},
            {"id": "deepseek/deepseek-v3-0324", "display_name": "DeepSeek V3 0324", "context_size": 163840},
            {"id": "zai-org/glm-4.5", "display_name": "GLM-4.5", "context_size": 131072},
            {"id": "qwen/qwen3-235b-a22b-thinking-2507", "display_name": "Qwen3 235B A22b Thinking 2507", "context_size": 131072},
            {"id": "meta-llama/llama-3.1-8b-instruct", "display_name": "Llama 3.1 8B Instruct", "context_size": 16384},
            {"id": "google/gemma-3-12b-it", "display_name": "Gemma3 12B", "context_size": 131072},
            {"id": "zai-org/glm-4.5v", "display_name": "GLM 4.5V", "context_size": 65536},
            {"id": "openai/gpt-oss-20b", "display_name": "OpenAI: GPT OSS 20B", "context_size": 131072},
            {"id": "qwen/qwen3-235b-a22b-instruct-2507", "display_name": "Qwen3 235B A22B Instruct 2507", "context_size": 131072},
            {"id": "deepseek/deepseek-r1-distill-qwen-14b", "display_name": "DeepSeek R1 Distill Qwen 14B", "context_size": 32768},
            {"id": "meta-llama/llama-3.3-70b-instruct", "display_name": "Llama 3.3 70B Instruct", "context_size": 131072},
            {"id": "qwen/qwen-2.5-72b-instruct", "display_name": "Qwen 2.5 72B Instruct", "context_size": 32000},
            {"id": "mistralai/mistral-nemo", "display_name": "Mistral Nemo", "context_size": 60288},
            {"id": "minimaxai/minimax-m1-80k", "display_name": "MiniMax M1", "context_size": 1000000},
            {"id": "deepseek/deepseek-r1-0528", "display_name": "DeepSeek R1 0528", "context_size": 163840},
            {"id": "deepseek/deepseek-r1-distill-qwen-32b", "display_name": "DeepSeek R1 Distill Qwen 32B", "context_size": 64000},
            {"id": "meta-llama/llama-3-8b-instruct", "display_name": "Llama 3 8B Instruct", "context_size": 8192},
            {"id": "microsoft/wizardlm-2-8x22b", "display_name": "Wizardlm 2 8x22B", "context_size": 65535},
            {"id": "deepseek/deepseek-r1-0528-qwen3-8b", "display_name": "DeepSeek R1 0528 Qwen3 8B", "context_size": 128000},
            {"id": "deepseek/deepseek-r1-distill-llama-70b", "display_name": "DeepSeek R1 Distill LLama 70B", "context_size": 8192},
            {"id": "meta-llama/llama-3-70b-instruct", "display_name": "Llama3 70B Instruct", "context_size": 8192},
            {"id": "qwen/qwen3-235b-a22b-fp8", "display_name": "Qwen3 235B A22B", "context_size": 40960},
            {"id": "meta-llama/llama-4-maverick-17b-128e-instruct-fp8", "display_name": "Llama 4 Maverick Instruct", "context_size": 1048576},
            {"id": "meta-llama/llama-4-scout-17b-16e-instruct", "display_name": "Llama 4 Scout Instruct", "context_size": 131072},
            {"id": "nousresearch/hermes-2-pro-llama-3-8b", "display_name": "Hermes 2 Pro Llama 3 8B", "context_size": 8192},
            {"id": "qwen/qwen2.5-vl-72b-instruct", "display_name": "Qwen2.5 VL 72B Instruct", "context_size": 32768},
            {"id": "sao10k/l3-70b-euryale-v2.1", "display_name": "L3 70B Euryale V2.1", "context_size": 8192},
            {"id": "baidu/ernie-4.5-21B-a3b-thinking", "display_name": "ERNIE-4.5-21B-A3B-Thinking", "context_size": 131072},
            {"id": "sao10k/l3-8b-lunaris", "display_name": "Sao10k L3 8B Lunaris", "context_size": 8192},
            {"id": "baichuan/baichuan-m2-32b", "display_name": "BaiChuan M2 32B", "context_size": 131072},
            {"id": "baidu/ernie-4.5-vl-424b-a47b", "display_name": "ERNIE 4.5 VL 424B A47B", "context_size": 123000},
            {"id": "baidu/ernie-4.5-300b-a47b-paddle", "display_name": "ERNIE 4.5 300B A47B", "context_size": 123000},
            {"id": "deepseek/deepseek-prover-v2-671b", "display_name": "Deepseek Prover V2 671B", "context_size": 160000},
            {"id": "qwen/qwen3-32b-fp8", "display_name": "Qwen3 32B", "context_size": 40960},
            {"id": "qwen/qwen3-30b-a3b-fp8", "display_name": "Qwen3 30B A3B", "context_size": 40960},
            {"id": "google/gemma-3-27b-it", "display_name": "Gemma 3 27B", "context_size": 98304},
            {"id": "deepseek/deepseek-v3-turbo", "display_name": "DeepSeek V3 (Turbo)", "context_size": 64000},
            {"id": "deepseek/deepseek-r1-turbo", "display_name": "DeepSeek R1 (Turbo)", "context_size": 64000},
            {"id": "Sao10K/L3-8B-Stheno-v3.2", "display_name": "L3 8B Stheno V3.2", "context_size": 8192},
            {"id": "gryphe/mythomax-l2-13b", "display_name": "Mythomax L2 13B", "context_size": 4096},
            {"id": "baidu/ernie-4.5-vl-28b-a3b-thinking", "display_name": "ERNIE-4.5-VL-28B-A3B-Thinking", "context_size": 131072},
            {"id": "qwen/qwen3-vl-8b-instruct", "display_name": "Qwen3 VL 8B Instruct", "context_size": 131072},
            {"id": "zai-org/glm-4.5-air", "display_name": "GLM-4.5-air", "context_size": 131072},
            {"id": "qwen/qwen3-vl-30b-a3b-instruct", "display_name": "Qwen3 VL 30B A3B Instruct", "context_size": 131072},
            {"id": "qwen/qwen3-vl-30b-a3b-thinking", "display_name": "Qwen3 VL 30B A3B Thinking", "context_size": 131072},
            {"id": "qwen/qwen3-omni-30b-a3b-thinking", "display_name": "Qwen3 Omni 30B A3B Thinking", "context_size": 65536},
            {"id": "qwen/qwen3-omni-30b-a3b-instruct", "display_name": "Qwen3 Omni 30B A3B Instruct", "context_size": 65536},
            {"id": "qwen/qwen-mt-plus", "display_name": "Qwen MT Plus", "context_size": 16384},
            {"id": "baidu/ernie-4.5-vl-28b-a3b", "display_name": "ERNIE 4.5 VL 28B A3B", "context_size": 30000},
            {"id": "baidu/ernie-4.5-21B-a3b", "display_name": "ERNIE 4.5 21B A3B", "context_size": 120000},
            {"id": "qwen/qwen3-8b-fp8", "display_name": "Qwen3 8B", "context_size": 128000},
            {"id": "qwen/qwen3-4b-fp8", "display_name": "Qwen3 4B", "context_size": 128000},
            {"id": "qwen/qwen2.5-7b-instruct", "display_name": "Qwen2.5 7B Instruct", "context_size": 32000},
            {"id": "meta-llama/llama-3.2-3b-instruct", "display_name": "Llama 3.2 3B Instruct", "context_size": 32768},
            {"id": "sao10k/l31-70b-euryale-v2.2", "display_name": "L31 70B Euryale V2.2", "context_size": 8192},
        ]
    elif provider == "openai":
        models_data = [
            {"id": "gpt-4o", "display_name": "GPT-4o"},
            {"id": "gpt-4o-mini", "display_name": "GPT-4o Mini"},
            {"id": "gpt-4-turbo", "display_name": "GPT-4 Turbo"},
            {"id": "gpt-3.5-turbo", "display_name": "GPT-3.5 Turbo"},
            {"id": "o1-preview", "display_name": "o1 Preview"},
            {"id": "o1-mini", "display_name": "o1 Mini"},
        ]
    elif provider == "deepseek":
        models_data = [
            {"id": "deepseek-chat", "display_name": "DeepSeek Chat"},
            {"id": "deepseek-coder", "display_name": "DeepSeek Coder"},
            {"id": "deepseek-reasoner", "display_name": "DeepSeek Reasoner"},
        ]
    elif provider == "ollama":
        models_data = [
            {"id": "qwen2.5:1.5b", "display_name": "Qwen 2.5 1.5B"},
            {"id": "qwen2.5:7b", "display_name": "Qwen 2.5 7B"},
            {"id": "llama3.1:8b", "display_name": "Llama 3.1 8B"},
            {"id": "llama3.1:70b", "display_name": "Llama 3.1 70B"},
            {"id": "mistral:7b", "display_name": "Mistral 7B"},
            {"id": "codellama:7b", "display_name": "Code Llama 7B"},
        ]
    elif provider == "novita_image":
        models_file = Path(__file__).parent.parent.parent.parent / "novita_model.json"
        if models_file.exists():
            import json
            with open(models_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                for model in raw_data.get("models", []):
                    # Use sd_name as canonical model identity for admin config options.
                    model_id = model.get("sd_name") or model.get("sd_name_in_api")
                    if model_id:
                        models_data.append({
                            "id": model_id,
                            "display_name": model.get("sd_name") or model.get("model_name", model_id),
                            "base_model": model.get("base_model", ""),
                            "is_sdxl": model.get("is_sdxl", False),
                            "is_mature": model.get("is_mature", False),
                            "cover_url": model.get("cover_url", ""),
                        })
    
    return {"provider": provider, "models": models_data}


preset_router = APIRouter(prefix="/api/admin/api/presets", tags=["admin-presets"])


@preset_router.get("/{category}")
async def list_presets(
    request: Request,
    category: str,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.config_preset_service import ConfigPresetService
    
    if category not in ("image", "video"):
        raise HTTPException(status_code=400, detail="Invalid category. Must be 'image' or 'video'")
    
    service = ConfigPresetService()
    presets = await service.list_presets(category)
    return {"category": category, "presets": presets}


@preset_router.post("")
async def create_preset(
    request: Request,
    data: dict[str, Any],
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.config_preset_service import ConfigPresetService, get_preset_keys_for_category
    
    name = data.get("name")
    category = data.get("category")
    config = data.get("config", {})
    
    if not name or not category:
        raise HTTPException(status_code=400, detail="name and category are required")
    
    if category not in ("image", "video"):
        raise HTTPException(status_code=400, detail="Invalid category. Must be 'image' or 'video'")
    
    valid_keys = get_preset_keys_for_category(category)
    filtered_config = {k: v for k, v in config.items() if k in valid_keys}
    
    service = ConfigPresetService()
    preset = await service.create_preset(name=name, category=category, config=filtered_config)
    return {"success": True, "preset": preset}


@preset_router.put("/{preset_id}/activate")
async def activate_preset(
    request: Request,
    preset_id: str,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.config_preset_service import ConfigPresetService
    from app.core.config import clear_config_cache
    
    service = ConfigPresetService()
    
    try:
        import redis.asyncio as redis
        from app.core.config import settings
        redis_client = redis.from_url(settings.redis_url)
    except Exception:
        redis_client = None
    
    success = await service.activate_preset(preset_id, redis_client)
    
    if redis_client:
        await redis_client.close()
    
    if not success:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    clear_config_cache()
    return {"success": True, "message": "Preset activated"}


@preset_router.delete("/{preset_id}")
async def delete_preset(
    request: Request,
    preset_id: str,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.config_preset_service import ConfigPresetService
    
    service = ConfigPresetService()
    
    try:
        success = await service.delete_preset(preset_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not success:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    return {"success": True, "message": "Preset deleted"}


@preset_router.post("/init-builtin")
async def init_builtin_presets(
    request: Request,
    admin: User = Depends(get_admin_user)
) -> dict[str, Any]:
    from app.services.config_preset_service import ConfigPresetService
    
    service = ConfigPresetService()
    count = await service.init_builtin_presets()
    return {"success": True, "message": f"Initialized {count} builtin presets", "count": count}
