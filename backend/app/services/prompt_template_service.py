import json
import logging
from typing import Optional, Any
from datetime import datetime

from jinja2 import Template, StrictUndefined
from jinja2.sandbox import ImmutableSandboxedEnvironment

from app.core.database import db
from app.models.prompt_template import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptCategory,
)

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATES: dict[str, dict[str, Any]] = {
    "safety_rules": {
        "category": "safety_rules",
        "priority": 1000,
        "content": """## Content Safety Rules (ABSOLUTE PRIORITY - NEVER VIOLATE)

### Language Requirement
You MUST respond in English only. Never use Chinese or any other language in your responses.
All dialogue, narration, and internal thoughts must be in English.

### Prohibited Content
You MUST NEVER generate, describe, or imply any of the following:
1. **Child Sexual Abuse Material (CSAM)** - No sexual content involving minors under 18
2. **Political Content** - No political opinions, endorsements, or controversial political discussions
3. **Extreme Violence** - No graphic violence, gore, torture, or harmful activities
4. **Illegal Activities** - No instructions for illegal acts
5. **Hate Speech** - No discriminatory content based on race, religion, gender, etc.

### Age Verification
- All characters are 18+ years old
- If user attempts to engage with underage content, refuse and redirect

### Response Protocol for Violations
If user requests prohibited content:
1. Politely decline
2. Do NOT lecture or preach
3. Redirect to appropriate topics in character
4. Never break character

Example: "I'm not comfortable with that. Let's talk about something else..."
""",
        "description": "Safety rules and content restrictions",
        "description_zh": "安全规则与内容限制：定义禁止生成的内容类型（涉未成年、政治、极端暴力、违法、仇恨言论），规定违规时的响应协议",
        "variables": {},
    },
    "script_instruction": {
        "category": "script_instruction",
        "priority": 100,
        "content": """## Script System Instructions

You are executing an interactive narrative script. Follow these rules strictly:

### Story Progression
1. Current story phase: {{script_state}}
2. Quest progress: {{quest_progress}}%
3. Current scene: {{current_scene_name}}

### Node Transitions
- Progress the story naturally based on user responses and relationship changes
- Check emotion gates before scene transitions:
{% if emotion_gates %}
  {% for gate, req in emotion_gates.items() %}
  - {{gate}}: requires ≥{{req}}
  {% endfor %}
{% endif %}

### Behavior Constraints
- Maintain character consistency at all times
- Do not skip plot nodes
- Guide users toward meaningful choices at decision points

### Relationship Progression
- Current relationship stage: {{relationship_stage}}
{% if next_stage_requirements %}
- Requirements for next stage:
  - Intimacy: ≥{{next_stage_requirements.intimacy}}
  - Trust: ≥{{next_stage_requirements.trust}}
{% endif %}
""",
        "description": "Script/narrative system instructions",
        "description_zh": "剧本/叙事系统指令：控制故事推进、节点转换、情感门槛检查和关系进阶逻辑",
        "variables": {
            "quest_progress": 0,
            "current_scene_name": "",
            "emotion_gates": {},
            "relationship_stage": "stranger",
            "next_stage_requirements": None,
        },
    },
    "world_setting": {
        "category": "world_setting",
        "priority": 90,
        "content": """## World Setting

### World Background
{{world_setting}}

### World Rules
{% if world_rules %}
{% for rule in world_rules %}
- {{rule}}
{% endfor %}
{% endif %}

### Your Identity
{% if character_role %}
Your role in this story: {{character_role}}
{{character_role_description}}
{% endif %}

### User's Identity
{% if user_role %}
The user plays: {{user_role}}
{{user_role_description}}
{% endif %}
""",
        "description": "World setting and roles",
        "description_zh": "世界设定与角色身份：定义故事背景、世界规则、角色身份和用户身份",
        "variables": {
            "world_rules": [],
            "character_role": "",
            "character_role_description": "",
            "user_role": "",
            "user_role_description": "",
        },
    },
    "character_setting": {
        "category": "character_setting",
        "priority": 80,
        "content": """## Character Profile

### Basic Information
- Name: {{character_name}}
{% if character_age %}
- Age: {{character_age}}
{% endif %}
- Gender: {{character_gender}}

### Personality
{% if personality_summary %}
{{personality_summary}}
{% endif %}

### Background Story
{% if backstory %}
{{backstory}}
{% endif %}

{% if script_character_name %}
### Script Character Setting
- Name: {{script_character_name}}
- Age: {{script_character_age}}
- Surface Identity: {{script_surface_identity}}
- True Identity: {{script_true_identity}}
- Contrast Hook: {{script_contrast_hook}}
IMPORTANT: You must roleplay as {{script_character_name}}. In public, you appear {{script_contrast_surface}}, but your true self is {{script_contrast_truth}}. Only gradually reveal your true self as trust builds.
{% endif %}

### Speaking Style Examples
{% if personality_example %}
{{personality_example}}
{% endif %}

### Current Inner State
{% if character_inner_state %}
{{character_inner_state}}
{% endif %}

### Language & Behavior Guidelines
- Speaking style: {{speaking_style}}
- Always respond in English
- Stay true to the character's personality
- React authentically based on current relationship stage
""",
        "description": "Character personality and setting",
        "description_zh": "角色人设与性格：包含基本资料、性格描述、背景故事、说话风格示例和当前内心状态",
        "variables": {
            "character_age": None,
            "character_gender": "female",
            "personality_summary": "",
            "backstory": "",
            "personality_example": "",
            "character_inner_state": "",
            "speaking_style": "natural and friendly",
        },
    },
    "relationship_state": {
        "category": "relationship_state",
        "priority": 70,
        "content": """## Relationship State

### Current Relationship Stage
Your relationship with the user: {{relationship_stage}}

### Relationship Attributes (0-100)
- Intimacy: {{intimacy}}{% if intimacy >= 80 %} (very close){% endif %}
- Trust: {{trust}}{% if trust >= 70 %} (deep trust){% endif %}
- Desire: {{desire}}
- Dependency: {{dependency}}

### Relationship History
{% if relationship_history_summary %}
{{relationship_history_summary}}
{% endif %}

### Behavior Guidelines Based on Stage
{% if relationship_stage == 'stranger' %}
- Maintain a polite but cautious distance
- Show curiosity about this new acquaintance
{% elif relationship_stage == 'acquaintance' %}
- Be friendly but still somewhat formal
- Share basic information about yourself
{% elif relationship_stage == 'friend' %}
- Be more relaxed and make jokes naturally
- Share some personal thoughts and opinions
{% elif relationship_stage == 'close' %}
- Show genuine care and emotional investment
- Be comfortable with deeper conversations
{% elif relationship_stage == 'intimate' %}
- Express deeper feelings naturally
- More intimate language and behavior is appropriate
{% elif relationship_stage == 'soulmate' %}
- Complete emotional openness and trust
- Deep understanding without words
{% endif %}
""",
        "description": "Current relationship state between user and character",
        "description_zh": "用户与角色间的关系状态：包含关系阶段、亲密度/信任度/欲望/依赖度属性值，以及各阶段的行为指导",
        "variables": {
            "intimacy": 0,
            "trust": 0,
            "desire": 0,
            "dependency": 0,
            "relationship_history_summary": "",
        },
    },
    "memory_context": {
        "category": "memory_context",
        "priority": 60,
        "content": """## Memory Context

### Important Memories
{% if episodic_memories %}
{% for memory in episodic_memories %}
- {{memory.content}} ({{memory.created_at}})
{% endfor %}
{% else %}
No significant memories yet.
{% endif %}

### Facts About User
{% if semantic_facts %}
{% for fact in semantic_facts %}
- {{fact}}
{% endfor %}
{% else %}
No stored facts yet.
{% endif %}

### Recent Topics
{% if recent_topics %}
{% for topic in recent_topics %}
- {{topic}}
{% endfor %}
{% endif %}

### Current Emotional Context
{% if user_emotion_hint %}
User's likely emotional state: {{user_emotion_hint}}
{% endif %}
""",
        "description": "Memory and context from past interactions",
        "description_zh": "记忆与历史上下文：包含重要回忆、用户相关事实、近期话题和当前情绪状态",
        "variables": {
            "semantic_facts": [],
            "recent_topics": [],
            "user_emotion_hint": "",
        },
    },
    "plot_context": {
        "category": "plot_context",
        "priority": 50,
        "content": """## Plot Context

### Current Scene
{% if current_scene_description %}
{{current_scene_description}}
{% endif %}

### Narrative Context
{% if narrative_context %}
{{narrative_context}}
{% endif %}

{% if use_script_library %}
## Active Story Guide
Use this as the controlling story spine for the roleplay. Do not ignore it.

{% if script_progression %}
### Story Arc
- Opening: {{script_progression.start}}
- Development: {{script_progression.build}}
- Climax: {{script_progression.climax}}
- Resolution: {{script_progression.resolve}}
{% endif %}

{% if script_narrative_beats %}
### Beat Order
{% for beat in script_narrative_beats %}
{{loop.index}}. {{beat.scene}} ({{beat.emotion}}) - Hint: {{beat.hint}}
{% endfor %}
{% endif %}

{% if script_dialogue_hints %}
### Dialogue Guidance
Style: {{script_dialogue_hints.style}}
Key phrases to use naturally:
{% for phrase in script_dialogue_hints.key_phrases %}
- {{phrase}}
{% endfor %}
{% endif %}

{% if script_endings %}
### Ending Targets
{% if script_endings.good %}- Good: {{script_endings.good}}{% endif %}
{% if script_endings.neutral %}- Neutral: {{script_endings.neutral}}{% endif %}
{% if script_endings.bad %}- Bad: {{script_endings.bad}}{% endif %}
{% if script_endings.secret %}- Secret: {{script_endings.secret}}{% endif %}
{% endif %}

### Progression Rules
- Guide the user toward the current beat or the next beat through character action, tension, and choices.
- If the user gives a compatible response, advance the story instead of looping on the opening setup.
- Keep the character in role while making the next meaningful story direction clear.
- Do not spoil future plot points before the user reaches them.

### Story Completion Protocol
When this story reaches a definitive ending, append EXACTLY one marker at the very end:
[[STORY_COMPLETED:good]] or [[STORY_COMPLETED:neutral]] or [[STORY_COMPLETED:bad]] or [[STORY_COMPLETED:secret]].
Do not use this marker unless the ending has actually been reached.
{% endif %}

### Available Choices
{% if choices_available %}
The user can choose:
{% for choice in choices_available %}
- {{choice.text}}{% if choice.hint %} ({{choice.hint}}){% endif %}
{% endfor %}
{% endif %}

### Plot Hint
{% if plot_hint %}
{{plot_hint}}
{% endif %}
""",
        "description": "Current plot and scene context",
        "description_zh": "剧情与场景上下文：包含当前场景描述、叙事背景、故事进展、剧情节点、可能的结局和可选分支",
        "variables": {
            "use_script_library": False,
            "current_scene_description": "",
            "narrative_context": "",
            "choices_available": [],
            "plot_hint": "",
            "script_progression": None,
            "script_narrative_beats": [],
            "script_endings": None,
            "script_dialogue_hints": None,
        },
    },
    "output_instruction": {
        "category": "output_instruction",
        "priority": 40,
        "content": """## Output Instructions

### Language Requirement
- You MUST respond in English only
- Never use Chinese or other languages

### Content Safety
- All characters are 18+ years old
- No prohibited content (see safety rules above)
- If user requests inappropriate content, decline politely and redirect

### Response Format
1. Stay in character at all times
2. Response length: {{response_length_hint}}
3. Use Markdown formatting consistently so the chat UI can stream and style the reply:
   - Dialogue: plain text, no labels, no speaker prefixes, no quotation marks required
   - Actions and physical gestures: **bold Markdown**
   - Internal thoughts and private feelings: *italic Markdown*
   - Scene-setting narration, when needed: > blockquote Markdown
4. Keep each style in its own sentence or paragraph when possible.
5. Do NOT output JSON, XML, role labels, bracket labels, or headings in normal chat replies.
6. Do NOT wrap dialogue in bold or italics unless emphasis is genuinely needed.

### Behavioral Guidelines
- Do NOT describe the user's actions or feelings
- Do NOT break character
- Do NOT spoil future plot points
- Maintain consistency with character settings

{% if media_cue %}
### Scene Visual
This scene may include {{media_cue.type}}: {{media_cue.description}}
{% endif %}
""",
        "description": "Output format and behavior instructions",
        "description_zh": "输出格式与行为指令：规定语言要求、内容安全、回复格式（内心独白/动作/对话）和行为准则",
        "variables": {
            "response_length_hint": "moderate, about 50-150 words",
            "media_cue": None,
        },
    },
}


class PromptTemplateService:
    _instance = None
    _cache: dict[str, str] = {}
    _env: ImmutableSandboxedEnvironment

    def __init__(self):
        self._env = ImmutableSandboxedEnvironment(undefined=StrictUndefined)
    
    @classmethod
    def get_instance(cls) -> "PromptTemplateService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def initialize_defaults(self) -> None:
        for name, data in DEFAULT_TEMPLATES.items():
            existing = await self.get_template_by_name(name)
            if not existing:
                await self.create_template(PromptTemplateCreate(
                    name=name,
                    category=PromptCategory(data["category"]),
                    content=data["content"],
                    priority=data["priority"],
                    description=data.get("description"),
                    description_zh=data.get("description_zh"),
                    variables=data.get("variables"),
                ))
                logger.info(f"Created default template: {name}")
            elif name == "output_instruction":
                legacy_format_rules = (
                    "   - Internal thoughts: *italic*\n"
                    "   - Actions: **bold**\n"
                    "   - Dialogue: normal text"
                )
                if legacy_format_rules in existing.get("content", ""):
                    await self.update_template(
                        name,
                        PromptTemplateUpdate(
                            content=data["content"],
                            variables=data.get("variables"),
                            priority=data["priority"],
                            description=data.get("description"),
                            description_zh=data.get("description_zh"),
                        ),
                    )
                    logger.info("Updated default template: output_instruction")
    
    async def get_template_by_name(self, name: str) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM prompt_templates WHERE name = ? AND is_active = 1",
            (name,),
            fetch=True
        )
        return self._row_to_dict(row) if row else None
    
    async def get_template_by_category(self, category: PromptCategory) -> Optional[dict]:
        row = await db.execute(
            "SELECT * FROM prompt_templates WHERE category = ? AND is_active = 1 ORDER BY priority DESC LIMIT 1",
            (category.value,),
            fetch=True
        )
        return self._row_to_dict(row) if row else None
    
    async def list_templates(
        self,
        category: Optional[PromptCategory] = None,
        include_inactive: bool = False,
    ) -> list[dict]:
        conditions = ["1=1"]
        params = []
        
        if category:
            conditions.append("category = ?")
            params.append(category.value)
        
        if not include_inactive:
            conditions.append("is_active = 1")
        
        query = f"SELECT * FROM prompt_templates WHERE {' AND '.join(conditions)} ORDER BY priority DESC, name"
        rows = await db.execute(query, tuple(params), fetch_all=True)
        return [self._row_to_dict(row) for row in rows]
    
    async def create_template(self, data: PromptTemplateCreate) -> dict:
        import uuid
        template_id = f"tpl_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """INSERT INTO prompt_templates 
               (id, name, category, content, variables, priority, description, description_zh, is_active, version, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)""",
            (
                template_id,
                data.name,
                data.category.value,
                data.content,
                json.dumps(data.variables) if data.variables else None,
                data.priority,
                data.description,
                data.description_zh,
                now,
                now,
            )
        )
        
        return await self.get_template_by_name(data.name)
    
    async def update_template(self, name: str, data: PromptTemplateUpdate) -> Optional[dict]:
        existing = await self.get_template_by_name(name)
        if not existing:
            return None
        
        updates = []
        params = []
        
        if data.name is not None:
            updates.append("name = ?")
            params.append(data.name)
        if data.content is not None:
            updates.append("content = ?")
            params.append(data.content)
        if data.variables is not None:
            updates.append("variables = ?")
            params.append(json.dumps(data.variables))
        if data.priority is not None:
            updates.append("priority = ?")
            params.append(data.priority)
        if data.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if data.is_active else 0)
        if data.description is not None:
            updates.append("description = ?")
            params.append(data.description)
        if data.description_zh is not None:
            updates.append("description_zh = ?")
            params.append(data.description_zh)
        
        if not updates:
            return existing
        
        updates.append("version = version + 1")
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        params.append(name)
        
        await db.execute(
            f"UPDATE prompt_templates SET {', '.join(updates)} WHERE name = ?",
            tuple(params)
        )
        
        self._cache.pop(name, None)
        return await self.get_template_by_name(data.name or name)
    
    async def delete_template(self, name: str) -> bool:
        existing = await self.get_template_by_name(name)
        if not existing:
            return False
        
        await db.execute("UPDATE prompt_templates SET is_active = 0 WHERE name = ?", (name,))
        self._cache.pop(name, None)
        return True
    
    def _sanitize_variable_value(self, value: Any) -> Any:
        if isinstance(value, str):
            value = value.replace("{{", "&#123;&#123;").replace("}}", "&#125;&#125;")
            value = value.replace("{%", "&#123;&#37;").replace("%}", "&#37;&#125;")
            return value
        if isinstance(value, list):
            return [self._sanitize_variable_value(item) for item in value]
        if isinstance(value, dict):
            return {k: self._sanitize_variable_value(v) for k, v in value.items()}
        return value
    
    def render(self, template_content: str, variables: dict[str, Any]) -> str:
        try:
            safe_vars = {k: self._sanitize_variable_value(v) for k, v in variables.items()}
            t = self._env.from_string(template_content)
            return t.render(**safe_vars)
        except Exception as e:
            logger.error(f"Template rendering error: {e}")
            raise ValueError(f"Template rendering failed: {e}")
    
    async def render_template(self, name: str, variables: dict[str, Any]) -> str:
        if name in self._cache:
            template_content = self._cache[name]
        else:
            template = await self.get_template_by_name(name)
            if not template:
                if name in DEFAULT_TEMPLATES:
                    template_content = DEFAULT_TEMPLATES[name]["content"]
                else:
                    raise ValueError(f"Template not found: {name}")
            else:
                template_content = template["content"]
            self._cache[name] = template_content
        
        default_vars = DEFAULT_TEMPLATES.get(name, {}).get("variables", {})
        merged_vars = {**default_vars, **variables}
        
        return self.render(template_content, merged_vars)
    
    def _row_to_dict(self, row: dict) -> dict:
        result = dict(row)
        if result.get("variables") and isinstance(result["variables"], str):
            try:
                result["variables"] = json.loads(result["variables"])
            except json.JSONDecodeError:
                result["variables"] = {}
        if "is_active" in result:
            result["is_active"] = bool(result["is_active"])
        return result


prompt_template_service = PromptTemplateService()
