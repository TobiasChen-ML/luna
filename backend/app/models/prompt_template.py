from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class PromptCategory(str, Enum):
    SCRIPT_INSTRUCTION = "script_instruction"
    WORLD_SETTING = "world_setting"
    CHARACTER_SETTING = "character_setting"
    RELATIONSHIP_STATE = "relationship_state"
    MEMORY_CONTEXT = "memory_context"
    PLOT_CONTEXT = "plot_context"
    OUTPUT_INSTRUCTION = "output_instruction"
    SAFETY_RULES = "safety_rules"


class PromptTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: PromptCategory
    content: str = Field(..., min_length=1)
    variables: Optional[dict[str, Any]] = None
    priority: int = Field(default=100, ge=1, le=1000)
    description: Optional[str] = None
    description_zh: Optional[str] = None


class PromptTemplateCreate(PromptTemplateBase):
    pass


class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    content: Optional[str] = Field(None, min_length=1)
    variables: Optional[dict[str, Any]] = None
    priority: Optional[int] = Field(None, ge=1, le=1000)
    is_active: Optional[bool] = None
    description: Optional[str] = None
    description_zh: Optional[str] = None


class PromptTemplate(PromptTemplateBase):
    id: str
    version: int = 1
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptTestRequest(BaseModel):
    variables: dict[str, Any] = Field(default_factory=dict)


class PromptTestResponse(BaseModel):
    rendered: str
    variables_used: list[str]
