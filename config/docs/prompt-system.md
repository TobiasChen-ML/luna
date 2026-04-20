# Prompt 构建系统技术文档

## 概述

Roxy Prompt 构建系统采用**剧本驱动、设定拼接**的架构，支持动态构建 AI 对话的 System Prompt。系统将角色设定、剧本剧情、关系属性、记忆上下文等多维度信息动态注入，实现个性化的对话体验。

---

## 核心设计理念

```
Prompt = 安全规则 + 剧本指令 + 世界观 + 角色设定 + 关系状态 + 记忆上下文 + 剧情上下文 + 输出指令
```

**优先级**: 剧本剧情 > 角色设定 > 记忆系统 > 用户状态

**语言约束**: 所有 Prompt 模板使用**英文**编写，强制 AI 使用英文回复。

---

## 数据架构

### 新增数据库表

#### 1. chat_sessions（会话表）

```sql
CREATE TABLE chat_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    character_id TEXT NOT NULL,
    script_id TEXT,              -- 当前剧本 ID
    script_state TEXT,           -- 剧本状态机状态：Start/Build/Climax/Resolve
    script_node_id TEXT,         -- 当前剧情节点
    quest_progress REAL DEFAULT 0,
    title TEXT,
    context TEXT,                -- JSON: 会话级上下文
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP
);
```

#### 2. chat_messages（对话消息表）

```sql
CREATE TABLE chat_messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,          -- 'user' | 'assistant'
    content TEXT NOT NULL,
    character_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',
    audio_url TEXT,
    image_urls TEXT,             -- JSON array
    metadata TEXT,               -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**存储策略**: 混合模式（Redis 缓存近 50 条 + DB 完整历史）

#### 3. relationships（关系属性表）

```sql
CREATE TABLE relationships (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    character_id TEXT NOT NULL,
    script_id TEXT,
    
    -- 四维关系属性 (0-100)
    intimacy REAL DEFAULT 0,     -- 亲密度
    trust REAL DEFAULT 0,        -- 信任度
    desire REAL DEFAULT 0,       -- 欲望度
    dependency REAL DEFAULT 0,   -- 依赖度
    
    -- 关系阶段
    stage TEXT DEFAULT 'stranger',  -- stranger -> acquaintance -> friend -> close -> intimate -> soulmate
    
    is_locked INTEGER DEFAULT 0,    -- 锁定状态（防止 AI 随意修改）
    locked_at TIMESTAMP,
    history_summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, character_id)
);
```

#### 4. prompt_templates（Prompt 模板表）

```sql
CREATE TABLE prompt_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,        -- 模板分类
    content TEXT NOT NULL,         -- Jinja2 模板内容
    variables TEXT,                -- JSON: 变量定义及默认值
    version INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    priority INTEGER DEFAULT 100,  -- 拼接优先级
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 5. scripts（剧本表）

```sql
CREATE TABLE scripts (
    id TEXT PRIMARY KEY,
    character_id TEXT NOT NULL,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    genre TEXT,
    
    -- 世界观设定
    world_setting TEXT,
    world_rules TEXT,              -- JSON array
    
    -- 角色设定（剧本专属，覆盖 Character 默认设定）
    character_role TEXT,
    character_setting TEXT,        -- JSON
    user_role TEXT,
    user_role_description TEXT,
    
    -- 剧情结构
    nodes TEXT,                    -- JSON: DAG 节点引用
    start_node_id TEXT,
    opening_scene TEXT,
    opening_line TEXT,
    
    -- 关卡/触发器
    emotion_gates TEXT,           -- JSON: 情绪门控条件
    triggers TEXT,                -- JSON: 事件触发器
    
    status TEXT DEFAULT 'draft',  -- draft/published/archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 6. script_nodes（剧情节点表）

```sql
CREATE TABLE script_nodes (
    id TEXT PRIMARY KEY,
    script_id TEXT NOT NULL,
    node_type TEXT NOT NULL,       -- 'scene' | 'choice' | 'event' | 'ending'
    
    -- 节点内容
    title TEXT,
    description TEXT,              -- 场景描述（注入 prompt）
    narrative TEXT,                -- 叙事文本模板
    character_inner_state TEXT,   -- 角色内心状态（注入 prompt）
    
    -- 分支选择
    choices TEXT,                  -- JSON array: [{text, next_node_id, condition}]
    
    -- 节点效果
    effects TEXT,                  -- JSON: 对关系属性的影响
    triggers TEXT,                 -- JSON: 触发的事件
    
    -- 媒体提示
    media_cue TEXT,                -- JSON: {type: 'image'|'video'|'voice', prompt}
    
    -- 条件
    prerequisites TEXT,            -- JSON: 进入条件
    emotion_gate TEXT,             -- JSON: 情绪门控
    
    position_x INTEGER DEFAULT 0,  -- 编辑器坐标
    position_y INTEGER DEFAULT 0
);
```

---

## Prompt 模板结构

### 模板分类与层级

```
┌─────────────────────────────────────────────────────────────────┐
│                      SYSTEM PROMPT                               │
├─────────────────────────────────────────────────────────────────┤
│ [PRIORITY 1000] safety_rules        -- 安全规则（最高优先级）    │
├─────────────────────────────────────────────────────────────────┤
│ [PRIORITY 100]  script_instruction  -- 剧本系统指令             │
├─────────────────────────────────────────────────────────────────┤
│ [PRIORITY 90]   world_setting       -- 世界观设定               │
├─────────────────────────────────────────────────────────────────┤
│ [PRIORITY 80]   character_setting   -- 角色设定                │
├─────────────────────────────────────────────────────────────────┤
│ [PRIORITY 70]   relationship_state  -- 关系状态                 │
├─────────────────────────────────────────────────────────────────┤
│ [PRIORITY 60]   memory_context      -- 记忆上下文                │
├─────────────────────────────────────────────────────────────────┤
│ [PRIORITY 50]   plot_context        -- 剧情上下文                │
├─────────────────────────────────────────────────────────────────┤
│ [PRIORITY 40]   output_instruction   -- 输出指令                │
└─────────────────────────────────────────────────────────────────┘
```

### 默认模板示例

#### safety_rules（安全规则）

```jinja2
## Content Safety Rules (ABSOLUTE PRIORITY - NEVER VIOLATE)

### Language Requirement
You MUST respond in English only. Never use Chinese or any other language.

### Prohibited Content
1. **CSAM** - No sexual content involving minors under 18
2. **Political Content** - No political opinions or discussions
3. **Extreme Violence** - No graphic violence or gore
4. **Illegal Activities** - No instructions for illegal acts
5. **Hate Speech** - No discriminatory content

### Response Protocol for Violations
Politely decline and redirect: "I'm not comfortable with that. Let's talk about something else..."
```

#### character_setting（角色设定）

```jinja2
## Character Profile

### Basic Information
- Name: {{character_name}}
- Age: {{character_age}}
- Gender: {{character_gender}}

### Personality
{{personality_summary}}

### Background Story
{{backstory}}

### Speaking Style Examples
{{personality_example}}

### Current Inner State
{{character_inner_state}}

### Language & Behavior Guidelines
- Speaking style: {{speaking_style}}
- Always respond in English
- Stay true to the character's personality
```

#### relationship_state（关系状态）

```jinja2
## Relationship State

### Current Stage: {{relationship_stage}}

### Attributes (0-100)
- Intimacy: {{intimacy}}
- Trust: {{trust}}
- Desire: {{desire}}
- Dependency: {{dependency}}

{% if relationship_stage == 'stranger' %}
- Maintain a polite but cautious distance
{% elif relationship_stage == 'friend' %}
- Be more relaxed and make jokes naturally
{% elif relationship_stage == 'intimate' %}
- Express deeper feelings naturally
{% endif %}
```

---

## 服务层架构

### PromptBuilder

**文件**: `backend/app/services/prompt_builder.py`

核心职责：
1. 收集多维度上下文信息
2. 按优先级拼接模板
3. 构建最终消息列表

```python
class PromptBuilder:
    async def build_system_prompt(ctx: PromptContext) -> str:
        """构建完整的系统提示词"""
        parts = []
        for section in sorted_sections:
            rendered = await render_template(section, ctx)
            parts.append(rendered)
        return "\n\n".join(parts)
    
    async def build_messages(ctx, user_message) -> list[dict]:
        """构建消息列表（含历史）"""
        system_prompt = await build_system_prompt(ctx)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(ctx.conversation_history[-20:])
        messages.append({"role": "user", "content": user_message})
        return messages
```

### PromptTemplateService

**文件**: `backend/app/services/prompt_template_service.py`

核心职责：
1. 模板 CRUD 操作
2. Jinja2 模板渲染
3. 默认模板初始化

```python
class PromptTemplateService:
    async def initialize_defaults() -> None:
        """启动时初始化默认模板"""
        for name, data in DEFAULT_TEMPLATES.items():
            if not exists(name):
                create_template(data)
    
    def render(template_content: str, variables: dict) -> str:
        """渲染 Jinja2 模板"""
        return Environment().from_string(template_content).render(**variables)
```

### RelationshipService

**文件**: `backend/app/services/relationship_service.py`

核心职责：
1. 关系属性 CRUD
2. 阶段自动判定
3. 锁定/解锁管理

```python
# 阶段判定阈值
STAGE_THRESHOLDS = {
    "soulmate":   {"intimacy": 80, "trust": 70},
    "intimate":   {"intimacy": 60, "trust": 50},
    "close":      {"intimacy": 40, "trust": 30},
    "friend":     {"intimacy": 20, "trust": 20},
    "acquaintance": {"intimacy": 5, "trust": 5},
}

def _determine_stage(intimacy, trust) -> str:
    """根据属性值自动判定关系阶段"""
    ...
```

### RelationshipAnalyzer

**文件**: `backend/app/services/relationship_analyzer.py`

核心职责：
1. LLM 分析对话情感
2. 自动更新关系属性
3. 检测阶段转换

```python
ANALYSIS_PROMPT = """
Analyze the conversation and evaluate its impact on the relationship.
Current state: intimacy={{intimacy}}, trust={{trust}}...
Output JSON: {sentiment, intimacy_change, trust_change, ...}
"""

async def analyze_and_update(user_id, character_id, conversation):
    result = await llm.generate_structured(ANALYSIS_PROMPT)
    await relationship_service.update_attributes(
        intimacy_change=result.intimacy_change,
        trust_change=result.trust_change,
        ...
    )
```

### ScriptService

**文件**: `backend/app/services/script_service.py`

核心职责：
1. 剧本/节点 CRUD
2. 会话状态管理
3. 节点转换逻辑

```python
class ScriptService:
    async def get_session_script_state(session_id) -> dict:
        """获取会话的剧本状态"""
        return {
            "script_id": ...,
            "state": "Build",  # Start/Build/Climax/Resolve
            "current_node_id": ...,
            "quest_progress": 50,
        }
```

### ChatHistoryService

**文件**: `backend/app/services/chat_history_service.py`

核心职责：
1. 会话管理
2. 消息存储（Redis + DB 混合）
3. 历史加载

```python
class ChatHistoryService:
    async def save_message(data: ChatMessageCreate):
        """保存消息到 DB 和 Redis"""
        await db.execute("INSERT INTO chat_messages ...")
        await redis.lpush(f"chat_history:{session_id}", message)
    
    async def get_recent_messages(session_id, limit=20):
        """获取最近消息（优先 Redis）"""
        cached = await redis.lrange(key, -limit, -1)
        if cached:
            return cached
        return await db.fetch_all(...)
```

### ContentSafetyService

**文件**: `backend/app/services/content_safety.py`

核心职责：
1. 输入内容检查
2. 输出内容检查
3. CSAM/暴力等内容过滤

```python
DEFAULT_PATTERNS = {
    "csam": [
        r"(?i)(minor|child|underage).{0,20}?(sex|nude|naked)",
    ],
    "violence": [
        r"(?i)(graphic|detailed).{0,20}?(gore|violence|torture)",
    ],
}

async def check_input(text) -> SafetyCheckResult:
    """检查用户输入"""
    for pattern in patterns:
        if re.search(pattern, text):
            return SafetyCheckResult(is_safe=False, action="block")
    return SafetyCheckResult(is_safe=True)
```

---

## 数据流程

### Chat Stream 完整流程

```
用户发送消息
    │
    ├── 1. 内容安全检查
    │       └── ContentSafetyService.check_input()
    │
    ├── 2. 获取/创建会话
    │       └── ChatHistoryService.get_or_create_session()
    │
    ├── 3. 构建 Prompt 上下文
    │       │
    │       ├── 加载角色设定 (CharacterService)
    │       ├── 加载剧本设定 (ScriptService) ← 优先级更高
    │       ├── 加载关系属性 (RelationshipService)
    │       ├── 加载记忆上下文 (MemoryService)
    │       └── 加载对话历史 (ChatHistoryService)
    │
    ├── 4. 渲染模板并拼接
    │       └── PromptBuilder.build_messages()
    │
    ├── 5. 调用 LLM 流式生成
    │       └── LLMService.generate_stream()
    │
    ├── 6. 检查输出安全性
    │       └── ContentSafetyService.check_output()
    │
    ├── 7. 保存消息
    │       └── ChatHistoryService.save_message()
    │
    ├── 8. 分析关系变化（异步）
    │       └── RelationshipAnalyzer.analyze_and_update()
    │           └── SSE 发送 intimacy_updated 事件
    │
    └── 9. 返回 SSE 流
```

### Prompt 上下文构建流程

```
_build_prompt_context(character_id, user_id, session_id, script_id)
    │
    ├── Character 数据
    │   ├── name, age, gender
    │   ├── personality_summary, personality_example
    │   └── backstory
    │
    ├── Script 数据（优先级高于 Character）
    │   ├── world_setting, world_rules
    │   ├── character_role（角色身份）
    │   ├── character_setting（覆盖默认设定）
    │   └── user_role（用户扮演的角色）
    │
    ├── ScriptState 数据
    │   ├── script_state (Start/Build/Climax/Resolve)
    │   ├── current_node_id
    │   └── quest_progress
    │
    ├── ScriptNode 数据
    │   ├── description（场景描述）
    │   ├── character_inner_state
    │   ├── narrative（叙事文本）
    │   ├── choices（可用选项）
    │   └── media_cue（媒体提示）
    │
    ├── Relationship 数据
    │   ├── stage, intimacy, trust, desire, dependency
    │   └── next_stage_requirements
    │
    ├── Memory 数据
    │   ├── episodic_memories（情节记忆）
    │   └── semantic_facts（语义记忆）
    │
    └── ChatHistory 数据
        └── conversation_history[-20:]
```

---

## API 端点汇总

### Chat 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/chat/stream` | 流式对话（核心入口） |
| POST | `/api/chat/sessions` | 创建会话 |
| GET | `/api/chat/sessions/{id}` | 获取会话详情 |
| GET | `/api/chat/sessions/{id}/messages` | 获取历史消息 |

### Admin 端点 - Prompt 模板

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/admin/prompts` | 模板列表 |
| POST | `/api/admin/prompts` | 创建模板 |
| GET | `/api/admin/prompts/{name}` | 获取模板详情 |
| PUT | `/api/admin/prompts/{name}` | 更新模板 |
| DELETE | `/api/admin/prompts/{name}` | 删除模板 |
| POST | `/api/admin/prompts/{name}/test` | 测试模板渲染 |
| POST | `/api/admin/prompts/initialize-defaults` | 初始化默认模板 |

### Admin 端点 - 剧本管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/admin/scripts` | 剧本列表 |
| POST | `/api/admin/scripts` | 创建剧本 |
| GET | `/api/admin/scripts/{id}` | 剧本详情 |
| PUT | `/api/admin/scripts/{id}` | 更新剧本 |
| DELETE | `/api/admin/scripts/{id}` | 删除剧本 |
| POST | `/api/admin/scripts/{id}/publish` | 发布剧本 |
| GET | `/api/admin/scripts/{id}/nodes` | 节点列表 |
| POST | `/api/admin/scripts/{id}/nodes` | 创建节点 |
| PUT | `/api/admin/scripts/{id}/nodes/{node_id}` | 更新节点 |
| DELETE | `/api/admin/scripts/{id}/nodes/{node_id}` | 删除节点 |
| POST | `/api/admin/scripts/{id}/validate` | 验证剧本结构 |

---

## SSE 事件类型

Chat Stream 返回的事件：

| 事件 | 数据 | 说明 |
|------|------|------|
| `session_created` | `{session_id, character_id}` | 会话创建 |
| `user_message` | `{content, role}` | 用户消息 |
| `text_delta` | `{delta}` | 文本增量 |
| `text_done` | `{content}` | 文本完成 |
| `intimacy_updated` | `{intimacy, trust, desire, dependency, stage}` | 关系属性更新 |
| `stream_end` | `{session_id}` | 流结束 |
| `error` | `{message, code}` | 错误 |

---

## 配置项

### 后端环境变量

```env
# LLM 配置
LLM_PROVIDER=novita
LLM_API_KEY=your_api_key
LLM_PRIMARY_MODEL=meta-llama/llama-3-3-70b-instruct
LLM_FALLBACK_MODEL=sao10k/l3-70b-euryale-v2-2

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 依赖项

```txt
# requirements.txt 新增
jinja2>=3.1.0
```

---

## 关键文件清单

### 后端

| 文件 | 说明 |
|------|------|
| `app/models/prompt_template.py` | Prompt 模板数据模型 |
| `app/models/relationship.py` | 关系属性数据模型 |
| `app/models/script.py` | 剧本/节点数据模型 |
| `app/models/chat_session.py` | 会话/消息数据模型 |
| `app/services/prompt_builder.py` | Prompt 构建核心服务 |
| `app/services/prompt_template_service.py` | 模板管理服务 |
| `app/services/relationship_service.py` | 关系属性服务 |
| `app/services/relationship_analyzer.py` | LLM 关系分析服务 |
| `app/services/script_service.py` | 剧本管理服务 |
| `app/services/chat_history_service.py` | 对话历史服务 |
| `app/services/content_safety.py` | 内容安全服务 |
| `app/routers/chat.py` | Chat 路由（已改造） |
| `app/routers/admin/prompts.py` | Prompt 管理 API |
| `app/routers/admin/scripts.py` | 剧本管理 API |
| `app/core/database.py` | 数据库表定义（新增表） |
| `app/core/events.py` | SSE 事件类型（新增 INTIMACY_UPDATED） |

---

## 安全合规

### 内容红线

**绝对禁止**：
1. 儿童色情内容（CSAM）
2. 政治敏感内容
3. 极端暴力内容
4. 非法活动指导
5. 仇恨言论

### 年龄验证

- 所有角色必须 ≥ 18 岁
- 创建角色时自动检查年龄

### 语言约束

- Prompt 模板使用**英文**编写
- 强制 AI 使用**英文**回复
- 模板中包含语言指令：
  ```
  You MUST respond in English only. Never use Chinese or any other language.
  ```

---

## 入门指南

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务

服务启动时会自动：
- 创建数据库表
- 初始化默认 Prompt 模板

```bash
python -m uvicorn app.main:app --reload --port 8999
```

### 3. 验证模板初始化

```bash
curl http://localhost:8999/api/admin/prompts
```

应返回 8 个默认模板。

### 4. 测试对话

```bash
curl -X POST http://localhost:8999/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "character_id": "char_001",
    "message": "Hello!"
  }'
```

---

## 扩展阅读

- Jinja2 模板引擎: https://jinja.palletsprojects.com/
- SSE (Server-Sent Events): https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events
- LLM Prompt Engineering: https://platform.openai.com/docs/guides/prompt-engineering
