import logging
from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum
from fastapi import HTTPException

from app.models.prompt_template import PromptCategory
from app.services.prompt_template_service import prompt_template_service
from app.services.prompt_sanitizer import prompt_sanitizer

logger = logging.getLogger(__name__)


class PromptSection(Enum):
    SAFETY_RULES = 1
    SCRIPT_INSTRUCTION = 2
    WORLD_SETTING = 3
    CHARACTER_SETTING = 4
    RELATIONSHIP_STATE = 5
    MEMORY_CONTEXT = 6
    PLOT_CONTEXT = 7
    OUTPUT_INSTRUCTION = 8


SECTION_TO_CATEGORY: dict[PromptSection, PromptCategory] = {
    PromptSection.SAFETY_RULES: PromptCategory.SAFETY_RULES,
    PromptSection.SCRIPT_INSTRUCTION: PromptCategory.SCRIPT_INSTRUCTION,
    PromptSection.WORLD_SETTING: PromptCategory.WORLD_SETTING,
    PromptSection.CHARACTER_SETTING: PromptCategory.CHARACTER_SETTING,
    PromptSection.RELATIONSHIP_STATE: PromptCategory.RELATIONSHIP_STATE,
    PromptSection.MEMORY_CONTEXT: PromptCategory.MEMORY_CONTEXT,
    PromptSection.PLOT_CONTEXT: PromptCategory.PLOT_CONTEXT,
    PromptSection.OUTPUT_INSTRUCTION: PromptCategory.OUTPUT_INSTRUCTION,
}


@dataclass
class PromptContext:
    character_id: str
    character_name: str = ""
    character_age: Optional[int] = None
    character_gender: str = "female"
    personality_summary: Optional[str] = None
    personality_example: Optional[str] = None
    backstory: Optional[str] = None
    speaking_style: str = "natural and friendly"
    
    script_id: Optional[str] = None
    script_state: Optional[str] = None
    current_node_id: Optional[str] = None
    quest_progress: float = 0.0
    
    world_setting: Optional[str] = None
    world_rules: list[str] = field(default_factory=list)
    character_role: Optional[str] = None
    character_role_description: Optional[str] = None
    user_role: Optional[str] = None
    user_role_description: Optional[str] = None
    
    current_scene_description: Optional[str] = None
    current_scene_name: str = ""
    character_inner_state: Optional[str] = None
    narrative_context: Optional[str] = None
    choices_available: list[dict] = field(default_factory=list)
    emotion_gates: Optional[dict] = None
    plot_hint: Optional[str] = None
    media_cue: Optional[dict] = None
    
    relationship_stage: str = "stranger"
    intimacy: float = 0.0
    trust: float = 0.0
    desire: float = 0.0
    dependency: float = 0.0
    relationship_history_summary: Optional[str] = None
    next_stage_requirements: Optional[dict] = None
    
    episodic_memories: list[dict] = field(default_factory=list)
    semantic_facts: list[str] = field(default_factory=list)
    recent_topics: list[str] = field(default_factory=list)
    user_emotion_hint: Optional[str] = None
    
    session_id: Optional[str] = None
    conversation_history: list[dict] = field(default_factory=list)
    
    response_length_hint: str = "moderate, about 50-150 words"
    enabled_sections: set[PromptSection] = field(
        default_factory=lambda: {
            PromptSection.SAFETY_RULES,
            PromptSection.CHARACTER_SETTING,
            PromptSection.RELATIONSHIP_STATE,
            PromptSection.OUTPUT_INSTRUCTION,
        }
    )
    
    script_library_seed: Optional[dict] = None
    script_library_full: Optional[dict] = None
    use_script_library: bool = False


class PromptBuilder:
    _instance = None
    
    def __init__(self):
        pass
    
    @classmethod
    def get_instance(cls) -> "PromptBuilder":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def build_system_prompt(
        self,
        ctx: PromptContext,
        sections: Optional[set[PromptSection]] = None,
    ) -> str:
        enabled = sections or ctx.enabled_sections
        parts = []
        
        sorted_sections = sorted(enabled, key=lambda s: s.value)
        
        for section in sorted_sections:
            category = SECTION_TO_CATEGORY.get(section)
            if not category:
                continue
            
            template_name = category.value
            
            try:
                variables = self._extract_variables(ctx, section)
                rendered = await prompt_template_service.render_template(template_name, variables)
                
                if rendered.strip():
                    parts.append(rendered)
            except Exception as e:
                logger.warning(f"Failed to render template {template_name}: {e}")
                continue

        if ctx.use_script_library:
            parts.append(
                "## Story Completion Protocol\n"
                "When this story reaches a definitive ending, append EXACTLY one marker at the very end:\n"
                "[[STORY_COMPLETED:good]] or [[STORY_COMPLETED:neutral]] or "
                "[[STORY_COMPLETED:bad]] or [[STORY_COMPLETED:secret]].\n"
                "Do not use this marker unless the ending has actually been reached."
            )
        
        return "\n\n".join(parts)
    
    def _extract_variables(self, ctx: PromptContext, section: PromptSection) -> dict[str, Any]:
        base_vars: dict[str, Any] = {}
        
        if section == PromptSection.SAFETY_RULES:
            pass
        
        elif section == PromptSection.SCRIPT_INSTRUCTION:
            base_vars = {
                "script_state": ctx.script_state or "Start",
                "quest_progress": ctx.quest_progress,
                "current_scene_name": ctx.current_scene_name,
                "emotion_gates": ctx.emotion_gates or {},
                "relationship_stage": ctx.relationship_stage,
                "next_stage_requirements": ctx.next_stage_requirements,
            }
        
        elif section == PromptSection.WORLD_SETTING:
            base_vars = {
                "world_setting": ctx.world_setting or "",
                "world_rules": ctx.world_rules or [],
                "character_role": ctx.character_role or "",
                "character_role_description": ctx.character_role_description or "",
                "user_role": ctx.user_role or "",
                "user_role_description": ctx.user_role_description or "",
            }
        
        elif section == PromptSection.CHARACTER_SETTING:
            base_vars = {
                "character_name": ctx.character_name,
                "character_age": ctx.character_age,
                "character_gender": ctx.character_gender,
                "personality_summary": ctx.personality_summary or "",
                "backstory": ctx.backstory or "",
                "personality_example": ctx.personality_example or "",
                "character_inner_state": ctx.character_inner_state or "",
                "speaking_style": ctx.speaking_style,
            }
            if ctx.use_script_library and ctx.script_library_seed:
                seed = ctx.script_library_seed
                char = seed.get("character", {})
                contrast = seed.get("contrast", {})
                if char:
                    base_vars["script_character_name"] = ctx.character_name or char.get("name", "")
                    base_vars["script_character_age"] = char.get("age", "")
                    base_vars["script_surface_identity"] = char.get("surface_identity", "")
                    base_vars["script_true_identity"] = char.get("true_identity", "")
                if contrast:
                    base_vars["script_contrast_surface"] = contrast.get("surface", "")
                    base_vars["script_contrast_truth"] = contrast.get("truth", "")
                    base_vars["script_contrast_hook"] = contrast.get("hook", "")
        
        elif section == PromptSection.RELATIONSHIP_STATE:
            base_vars = {
                "relationship_stage": ctx.relationship_stage,
                "intimacy": ctx.intimacy,
                "trust": ctx.trust,
                "desire": ctx.desire,
                "dependency": ctx.dependency,
                "relationship_history_summary": ctx.relationship_history_summary or "",
            }
        
        elif section == PromptSection.MEMORY_CONTEXT:
            base_vars = {
                "episodic_memories": ctx.episodic_memories or [],
                "semantic_facts": ctx.semantic_facts or [],
                "recent_topics": ctx.recent_topics or [],
                "user_emotion_hint": ctx.user_emotion_hint or "",
            }
        
        elif section == PromptSection.PLOT_CONTEXT:
            base_vars = {
                "current_scene_description": ctx.current_scene_description or "",
                "narrative_context": ctx.narrative_context or "",
                "choices_available": ctx.choices_available or [],
                "plot_hint": ctx.plot_hint or "",
            }
            if ctx.use_script_library and ctx.script_library_full:
                full = ctx.script_library_full
                progression = ctx.script_library_seed.get("progression", {}) if ctx.script_library_seed else {}
                beats = full.get("narrative_beats", [])
                endings = ctx.script_library_seed.get("endings", {}) if ctx.script_library_seed else {}
                dialogue_hints = full.get("dialogue_hints", {})
                base_vars["script_progression"] = progression
                base_vars["script_narrative_beats"] = beats
                base_vars["script_endings"] = endings
                base_vars["script_dialogue_hints"] = dialogue_hints
        
        elif section == PromptSection.OUTPUT_INSTRUCTION:
            base_vars = {
                "response_length_hint": ctx.response_length_hint,
                "media_cue": ctx.media_cue,
            }
        
        return base_vars
    
    async def build_messages(
        self,
        ctx: PromptContext,
        user_message: str,
        include_history: bool = True,
    ) -> list[dict]:
        sanitization_result = prompt_sanitizer.sanitize_user_input(user_message)
        if sanitization_result.injection_detected:
            pattern_preview = (sanitization_result.matched_pattern or "unknown")[:30]
            logger.warning(
                f"Prompt injection attempt detected in session {ctx.session_id}: "
                f"pattern={pattern_preview}..."
            )
            raise HTTPException(
                status_code=400,
                detail="Invalid input detected. Please rephrase your message."
            )
        
        system_prompt = await self.build_system_prompt(ctx)
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if include_history and ctx.conversation_history:
            for msg in ctx.conversation_history[-20:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", ""),
                })
        
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def create_context(
        self,
        character_id: str,
        character_name: str = "",
        **kwargs,
    ) -> PromptContext:
        return PromptContext(
            character_id=character_id,
            character_name=character_name,
            **kwargs,
        )


prompt_builder = PromptBuilder()
