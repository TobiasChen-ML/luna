"""
Script Library Data Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class ScriptLibraryStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ScriptSeedCharacter(BaseModel):
    name: str
    age: int
    surface_identity: str
    true_identity: str
    profession: str


class ScriptSeedContrast(BaseModel):
    surface: str
    truth: str
    hook: str


class ScriptSeedProgression(BaseModel):
    start: str
    build: str
    climax: str
    resolve: str


class ScriptSeedKeyNode(BaseModel):
    name: str
    description: str
    trigger: str


class ScriptSeedEndings(BaseModel):
    good: str
    neutral: str
    bad: str
    secret: str


class ScriptSeed(BaseModel):
    character: ScriptSeedCharacter
    contrast: ScriptSeedContrast
    progression: ScriptSeedProgression
    key_nodes: List[ScriptSeedKeyNode]
    endings: ScriptSeedEndings


class ScriptLibraryBase(BaseModel):
    title: str
    title_en: Optional[str] = None
    summary: Optional[str] = None
    
    emotion_tones: List[str] = []
    relation_types: List[str] = []
    contrast_types: List[str] = []
    era: Optional[str] = None
    gender_target: Optional[str] = None
    character_gender: Optional[str] = None
    profession: Optional[str] = None
    length: Optional[str] = None
    age_rating: Optional[str] = None
    
    contrast_surface: Optional[str] = None
    contrast_truth: Optional[str] = None
    contrast_hook: Optional[str] = None
    
    script_seed: Optional[ScriptSeed] = None
    full_script: Optional[Dict[str, Any]] = None


class ScriptLibraryCreate(ScriptLibraryBase):
    pass


class ScriptLibraryUpdate(BaseModel):
    title: Optional[str] = None
    title_en: Optional[str] = None
    summary: Optional[str] = None
    emotion_tones: Optional[List[str]] = None
    relation_types: Optional[List[str]] = None
    contrast_types: Optional[List[str]] = None
    era: Optional[str] = None
    gender_target: Optional[str] = None
    character_gender: Optional[str] = None
    profession: Optional[str] = None
    length: Optional[str] = None
    age_rating: Optional[str] = None
    contrast_surface: Optional[str] = None
    contrast_truth: Optional[str] = None
    contrast_hook: Optional[str] = None
    script_seed: Optional[ScriptSeed] = None
    full_script: Optional[Dict[str, Any]] = None
    status: Optional[ScriptLibraryStatus] = None


class ScriptLibrary(ScriptLibraryBase):
    id: str
    popularity: int = 0
    status: ScriptLibraryStatus = ScriptLibraryStatus.DRAFT
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ScriptLibraryListResponse(BaseModel):
    items: List[ScriptLibrary]
    total: int
    page: int
    page_size: int


class ScriptTag(BaseModel):
    id: str
    category: str
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    examples: List[str] = []
    parent_id: Optional[str] = None


class ScriptTagsByCategory(BaseModel):
    emotion_tones: List[ScriptTag] = []
    relation_types: List[ScriptTag] = []
    contrast_types: List[ScriptTag] = []
    eras: List[ScriptTag] = []
    professions: List[ScriptTag] = []
    gender_targets: List[ScriptTag] = []
    character_genders: List[ScriptTag] = []
    lengths: List[ScriptTag] = []
    age_ratings: List[ScriptTag] = []
