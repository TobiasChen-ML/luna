import logging
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException
from typing import Any, Optional

from app.models import BaseResponse, PromptCategory
from app.models.prompt_template import PromptTemplateCreate, PromptTemplateUpdate, PromptTestRequest
from app.services.prompt_template_service import prompt_template_service
from app.services.prompt_builder import prompt_builder

router = APIRouter(prefix="/api/admin/prompts", tags=["admin-prompts"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_prompts(
    request: Request,
    category: Optional[str] = None,
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    cat = PromptCategory(category) if category else None
    templates = await prompt_template_service.list_templates(
        category=cat,
        include_inactive=include_inactive,
    )
    return templates


@router.post("")
async def create_prompt(
    request: Request,
    data: PromptTemplateCreate,
) -> dict[str, Any]:
    existing = await prompt_template_service.get_template_by_name(data.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Template '{data.name}' already exists")
    
    template = await prompt_template_service.create_template(data)
    return template


@router.get("/{name}")
async def get_prompt(request: Request, name: str) -> dict[str, Any]:
    template = await prompt_template_service.get_template_by_name(name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")
    return template


@router.put("/{name}")
async def update_prompt(
    request: Request,
    name: str,
    data: PromptTemplateUpdate,
) -> dict[str, Any]:
    template = await prompt_template_service.update_template(name, data)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")
    return template


@router.delete("/{name}", response_model=BaseResponse)
async def delete_prompt(request: Request, name: str) -> BaseResponse:
    success = await prompt_template_service.delete_template(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")
    return BaseResponse(success=True, message=f"Template '{name}' deactivated")


@router.post("/{name}/test")
async def test_prompt(
    request: Request,
    name: str,
    data: PromptTestRequest,
) -> dict[str, Any]:
    template = await prompt_template_service.get_template_by_name(name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{name}' not found")
    
    try:
        rendered = prompt_template_service.render(template["content"], data.variables)
        return {
            "template_name": name,
            "rendered": rendered,
            "variables_used": list(data.variables.keys()),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Rendering failed: {str(e)}")


@router.post("/initialize-defaults", response_model=BaseResponse)
async def initialize_defaults(request: Request) -> BaseResponse:
    await prompt_template_service.initialize_defaults()
    return BaseResponse(success=True, message="Default templates initialized")


@router.get("/categories")
async def list_categories(request: Request) -> list[dict[str, str]]:
    return [
        {"value": c.value, "label": c.value.replace("_", " ").title()}
        for c in PromptCategory
    ]
