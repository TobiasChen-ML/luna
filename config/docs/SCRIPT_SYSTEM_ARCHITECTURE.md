# 剧本系统架构文档

> 版本: v2.1  
> 更新日期: 2026-04-17  
> 作者: AI Development Team
> 
> **v2.1 更新**: 新增剧本库系统 (Script Library)，145+ 剧本模板，9 维度分类，157 标签

---

## 目录

1. [设计理念](#1-设计理念)
2. [核心数据模型](#2-核心数据模型)
3. [关系系统](#3-关系系统)
4. [剧情推进](#4-剧情推进)
5. [AI 如何主导叙事](#5-ai-如何主导叙事)
6. [剧本节点作为 AI 指导](#6-剧本节点作为-ai-指导)
7. [多结局系统](#7-多结局系统)
8. [媒体触发器](#8-媒体触发器)
9. [API 参考](#9-api-参考)
10. [关键文件](#10-关键文件)
11. [剧本库系统](#11-剧本库系统-script-library)

---

## 1. 设计理念

### 1.1 核心原则：AI 主导叙事

与传统的选择式游戏不同（用户点击按钮选择剧情分支），Roxy 的剧本系统设计围绕 **AI 角色主动引导用户完成故事**。

**AI 角色：**
- 通过自然对话主动推进剧情
- 根据用户对话内容和关系动态做出响应
- 引导故事走向关键时刻
- 决定何时切换剧情阶段

**用户：**
- 进行自然对话
- 自然地体验故事
- 无需点击预定义的选择按钮
- 通过语言和关系建设影响故事走向

### 1.2 关键设计决策

| 决策 | 理由 |
|------|------|
| **无显式选择按钮** | 保持沉浸感，像真实对话 |
| **关系门槛推进** | 亲密度/信任度自然解锁剧情阶段 |
| **节点作为 AI 上下文** | 剧本节点指导 AI，而非用户 UI |
| **自然语言流程** | 剧情通过有机对话推进 |

### 1.3 用户体验对比

```
传统游戏：
  用户看到：[选项 A] [选项 B] [选项 C]
  用户点击：[选项 A]
  系统："你选择了 A"

Roxy 剧本系统：
  用户说："我一直想告诉你一件事..."
  AI 角色：自然响应，根据上下文推进剧情
  用户感受：像真正的对话
```

---

## 2. 核心数据模型

### 2.1 剧本（故事定义）

剧本定义了附着于角色的完整叙事体验。

| 字段 | 用途 |
|------|------|
| `character_id` | 主导此故事的 AI 角色 |
| `title` | 故事标题 |
| `world_setting` | 背景世界描述 |
| `world_rules` | AI 必须遵循的规则（JSON 数组） |
| `character_role` | 角色在故事中的身份 |
| `user_role` | 用户在故事中的身份 |
| `opening_scene` | 开场场景描述 |
| `opening_line` | 角色的第一句话 |
| `emotion_gates` | 阶段切换的要求 |

### 2.2 剧本节点（AI 指导上下文）

节点提供 **AI 的上下文**，而非用户可点击的选择。

| 字段 | 用途 |
|------|------|
| `node_type` | `scene`（场景）、`choice`（选择）、`event`（事件）、`ending`（结局） |
| `title` | 场景名称（供 AI 参考） |
| `description` | AI 应融入对话的场景细节 |
| `narrative` | AI 应编织进对话的剧情要点 |
| `character_inner_state` | 角色此刻的想法/感受 |
| `choices` | AI 可引导的方向 |
| `effects` | 到达此节点时的关系变化 |
| `emotion_gate` | 进入此场景的要求 |

**重要**：`choices` 字段**不会**显示为按钮。它帮助 AI 理解叙事可能性，自然引导对话。

### 2.3 节点类型

| 类型 | 用途 | AI 行为 |
|------|------|---------|
| `scene` | 故事时刻 | AI 将场景细节融入对话 |
| `choice` | 决策点 | AI 引导对话走向某个选项方向 |
| `event` | 剧情事件 | AI 触发特殊叙事时刻 |
| `ending` | 故事结局 | AI 收尾故事，确定结局类型 |

### 2.4 会话状态

记录在 `chat_sessions` 表中：

| 字段 | 用途 |
|------|------|
| `script_id` | 本次对话的活跃剧本 |
| `script_state` | 当前阶段（Start/Build/Climax/Resolve） |
| `script_node_id` | 当前故事节点 |
| `quest_progress` | 0-100 完成百分比 |
| `context` | JSON，包含 `visited_nodes` 等变量 |

---

## 3. 关系系统

### 3.1 关系属性

| 属性 | 范围 | 用途 |
|------|------|------|
| `intimacy` | 0-100 | 情感亲密度，解锁更深内容 |
| `trust` | 0-100 | 对角色的信任度，影响分享意愿 |
| `desire` | 0-100 | 身体吸引力 |
| `dependency` | 0-100 | 情感依赖度 |

### 3.2 关系阶段

用户与角色的关系逐步升级：

```
陌生人 → 相识 → 朋友 → 亲密 → 深交 → 知己
stranger → acquaintance → friend → close → intimate → soulmate
```

### 3.3 阶段阈值

| 阶段 | 亲密度 | 信任度 | 角色行为 |
|------|----------|-------|----------|
| `stranger` | 0 | 0 | 礼貌但疏远，好奇 |
| `acquaintance` | 5 | 5 | 友好但正式 |
| `friend` | 20 | 20 | 放松，开玩笑，分享想法 |
| `close` | 40 | 30 | 真诚关心，深入交流 |
| `intimate` | 60 | 50 | 表达深层情感，亲密语言 |
| `soulmate` | 80 | 70 | 完全敞开，无言的理解 |

### 3.4 关系如何影响故事

- **低亲密度**：AI 保持对话在表层
- **亲密度增长**：AI 逐渐分享更多个人想法
- **高亲密度**：AI 敞开心扉，谈论感受、秘密
- **信任门槛**：某些剧情阶段需要最低信任等级

---

## 4. 剧情推进

### 4.1 故事阶段

```
开场 (0-20%) → 发展 (20-60%) → 高潮 (60-85%) → 结局 (85-100%)
Start → Build → Climax → Resolve
```

| 阶段 | 描述 | 典型亲密度 |
|------|------|------------|
| **Start** | 初识，第一印象 | 0-5 |
| **Build** | 关系发展 | 5-50 |
| **Climax** | 冲突、揭示、转折点 | 50-70 |
| **Resolve** | 解决、结局 | 70+ |

### 4.2 情感门槛

每个阶段有要求，AI 必须在用户达到后才可推进：

```json
{
  "emotion_gates": {
    "Start":  {"intimacy": 0,  "trust": 0},
    "Build":  {"intimacy": 20, "trust": 15},
    "Climax": {"intimacy": 50, "trust": 40},
    "Resolve": {"intimacy": 70, "trust": 60}
  }
}
```

### 4.3 任务进度

- `quest_progress`：0-100 值追踪故事完成度
- AI 根据对话里程碑更新
- 决定阶段切换时机
- 向用户显示进度指示

---

## 5. AI 如何主导叙事

### 5.1 提示词上下文注入

当用户处于剧本会话中，以下上下文注入到 AI 的系统提示词：

```
## 剧本系统指令

你正在执行一个交互式叙事剧本。严格遵循以下规则：

### 故事推进
1. 当前故事阶段：{{script_state}}
2. 任务进度：{{quest_progress}}%
3. 当前场景：{{current_scene_name}}

### 节点切换
- 根据用户回应和关系变化自然推进故事
- 场景切换前检查情感门槛

### 行为约束
- 始终保持角色一致性
- 不要跳过剧情节点
- 在决策点引导用户走向有意义的选择

### 关系推进
- 当前关系阶段：{{relationship_stage}}
- 下一阶段要求：
  - 亲密度：≥{{next_stage_requirements.intimacy}}
  - 信任度：≥{{next_stage_requirements.trust}}
```

### 5.2 剧情上下文部分

```
## 剧情上下文

### 当前场景
{{current_scene_description}}

### 叙事背景
{{narrative_context}}

### 可选方向
{% if choices_available %}
故事可以走向：
{% for choice in choices_available %}
- {{choice.text}}
{% endfor %}
{% endif %}
```

### 5.3 AI 决策过程

AI 使用此上下文：

1. **理解当前场景** - 发生什么，角色感受如何
2. **知晓可选方向** - 故事接下来可以去哪里
3. **检查关系门槛** - 用户是否准备好进入下一阶段
4. **自然推进** - 引导对话走向剧情里程碑

### 5.4 AI 行为示例

**场景**：咖啡店初次相遇  
**节点上下文**："她感到孤独，希望有人搭话"  
**可选方向**：["开始对话", "保持沉默"]

**用户说**："这里有人坐吗？"

**AI 回应**："没有，请坐。*她抬头微笑，感激有人陪伴。* 我刚才在看雨..."

*AI 自然引导向"开始对话"方向，无需显示按钮。*

---

## 6. 剧本节点作为 AI 指导

### 6.1 场景节点示例

```json
{
  "id": "node_first_meeting",
  "node_type": "scene",
  "title": "咖啡店偶遇",
  "description": "雨夜安静的咖啡店",
  "narrative": "她独自坐在窗边，看着雨",
  "character_inner_state": "感到孤独，期待有人搭话",
  "emotion_gate": {"intimacy": 0, "trust": 0}
}
```

**AI 用途**：设定场景，理解角色情绪，自然回应

### 6.2 选择节点示例

```json
{
  "id": "node_confession_moment",
  "node_type": "choice",
  "title": "告白时刻",
  "description": "月光下，你们沉默相对",
  "choices": [
    {
      "text": "表白心意",
      "next_node_id": "node_good_ending",
      "effects": {"intimacy": 10, "trust": 5},
      "conditions": {"min_intimacy": 50}
    },
    {
      "text": "保持沉默",
      "next_node_id": "node_neutral_ending",
      "effects": {"trust": -5}
    }
  ]
}
```

**AI 用途**：
- 理解这是关键时刻
- 知晓故事可走向好结局或中性结局
- 检查用户是否有足够亲密度（50+）进入告白路线
- 根据用户话语自然引导对话

### 6.3 结局节点示例

```json
{
  "id": "node_good_ending",
  "node_type": "ending",
  "title": "幸福结局",
  "description": "她轻轻握住你的手",
  "narrative": "从那天起，你们的故事开启了新篇章",
  "ending_type": "good",
  "effects": {"trust_bonus": 10, "intimacy_bonus": 15}
}
```

**AI 用途**：收尾故事，呈现结局叙事，应用奖励

---

## 7. 多结局系统

### 7.1 结局类型

| 类型 | 条件 | 关系奖励 |
|------|------|----------|
| `good` | 高亲密度 + 信任度 | trust +10, intimacy +15 |
| `neutral` | 中等关系值 | trust +5, intimacy +5 |
| `bad` | 低关系值或糟糕选择 | 无奖励 |
| `secret` | 满足隐藏条件 | trust +15, intimacy +20 |

### 7.2 结局如何判定

AI 根据以下判定结局：

1. **当前关系值** - 亲密度和信任度水平
2. **全程选择** - 累积的效果
3. **故事路径** - 访问了哪些节点
4. **节点预定义 ending_type** - 某些结局是节点特定的

### 7.3 结局流程

```
AI 到达结局节点
       │
       ▼
从节点获取 ending_type
       │
       ▼
计算奖励：
  - 基础奖励（来自 ending_type）
  - 累积效果（来自选择）
       │
       ▼
应用奖励到关系
       │
       ▼
呈现结局叙事
       │
       ▼
标记故事已完成
```

---

## 8. 媒体触发器

### 8.1 概述

媒体触发器允许用户在故事关键时刻请求生成图片/视频。

### 8.2 触发策略

- **用户主动触发**：用户点击按钮请求生成
- **成本效率**：仅在用户需要时生成
- **上下文感知**：使用场景描述作为提示词

### 8.3 媒体触发结构

```json
{
  "cue_id": "cue_sunset_001",
  "type": "image",
  "prompt": "浪漫夕阳海滩场景，两个剪影，金色时刻",
  "trigger_at_progress": 65,
  "trigger_stage": "Climax",
  "min_intimacy": 60
}
```

### 8.4 触发条件

- 用户必须达到最低亲密度
- 触发器之前未被触发
- 用户明确请求生成

---

## 9. API 参考

### 9.1 剧本端点

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/scripts` | 列出所有剧本 |
| POST | `/api/scripts` | 创建剧本 |
| GET | `/api/scripts/{id}` | 获取剧本详情 |
| PUT | `/api/scripts/{id}` | 更新剧本 |
| DELETE | `/api/scripts/{id}` | 删除剧本 |
| GET | `/api/scripts/character/{char_id}` | 获取角色的剧本 |
| POST | `/api/scripts/{id}/start` | 开始剧本会话 |
| GET | `/api/scripts/{id}/progress` | 获取进度 |
| GET | `/api/scripts/{id}/gates` | 检查情感门槛 |
| POST | `/api/scripts/{id}/media/trigger` | 触发媒体生成 |

### 9.2 SSE 事件

| 事件 | 描述 |
|------|------|
| `script_state_updated` | 故事阶段变更 |
| `quest_progress_updated` | 进度百分比更新 |
| `intimacy_updated` | 关系值变更 |
| `media_cue_triggered` | 媒体生成触发 |

---

## 10. 关键文件

| 组件 | 路径 |
|------|------|
| 数据库结构 | `backend/app/core/database.py` |
| 剧本模型 | `backend/app/models/script.py` |
| 剧本服务 | `backend/app/services/script_service.py` |
| 关系服务 | `backend/app/services/relationship_service.py` |
| 提示词构建器 | `backend/app/services/prompt_builder.py` |
| 提示词模板 | `backend/app/services/prompt_template_service.py` |
| 聊天路由 | `backend/app/routers/chat.py` |
| 剧本路由 | `backend/app/routers/scripts.py` |
| 剧本库路由 | `backend/app/routers/script_library.py` |
| 前端服务 | `frontend/src/services/scriptService.ts` |
| 类型定义 | `frontend/src/types/script.ts` |
| 剧本编辑器 | `frontend/src/components/script/ScriptEditor.tsx` |
| DAG 编辑器 | `frontend/src/components/script/DagEditor/DagEditor.tsx` |

---

## 11. 剧本库系统 (Script Library)

### 11.1 概述

剧本库是一个可搜索的故事模板数据库，包含 **145+ 个预定义剧本**，涵盖 **9 个情感维度** 和 **157 个分类标签**。

### 11.2 剧本分类维度

| 维度 | 说明 | 示例标签 |
|------|------|----------|
| **emotion_tones** | 情感基调 | `angst`(虐恋), `sweet`(甜宠), `comedy`(喜剧), `dark`(暗黑), `healing`(治愈), `suspense`(悬疑), `rebirth`(重生), `revenge`(复仇), `harem`(后宫) |
| **relation_types** | 关系类型 | `boss_subordinate`(上司下属), `teacher_student`(师生), `childhood_friends`(青梅竹马), `enemies_to_lovers`(相爱相杀), `captor_captive`(囚禁关系) 等 |
| **contrast_types** | 反差类型 | `identity`(身份反差), `personality`(性格反差), `power`(权力反差), `relationship`(关系反差), `memory`(记忆反差) |
| **era** | 时代背景 | `modern_urban`(现代都市), `modern_campus`(现代校园), `ancient_palace`(古代宫廷), `ancient_jianghu`(古代江湖), `republic_warlord`(民国军阀), `future_cyberpunk`(未来赛博) 等 |
| **gender_target** | 目标用户 | `female`(女性向), `male`(男性向), `general`(通用) |
| **character_gender** | 角色性别 | `male_char`(男性角色), `female_char`(女性角色) |
| **profession** | 职业类型 | `business`(商界), `entertainment`(娱乐圈), `medical`(医疗), `campus`(校园), `crime`(黑道) 等 |
| **length** | 故事长度 | `short`(短篇), `medium`(中篇), `long`(长篇) |
| **age_rating** | 年龄分级 | `all`(全年龄), `adult`(成人) |

### 11.3 剧本结构

每个剧本包含：

```json
{
  "id": "angst_001",
  "title": "替身情人",
  "title_en": "Substitute Lover",
  "summary": "他把你当她的替身，你却动了真心",
  "emotion_tones": ["angst"],
  "relation_types": ["contract_lovers", "substitute"],
  "contrast_types": ["relationship", "expectation_reality"],
  "era": "modern_urban",
  "gender_target": "female",
  "character_gender": "male_char",
  "profession": "business",
  "length": "medium",
  "age_rating": "adult",
  "contrast_surface": "他对你温柔体贴，满足你一切物质需求",
  "contrast_truth": "他只是把你当作前女友的替身，从未真正爱你",
  "contrast_hook": "当你发现真相后，他却开始慌了",
  "script_seed": {
    "character": { "name": "陆景深", "age": 29, ... },
    "contrast": { "surface": "...", "truth": "...", "hook": "..." },
    "progression": { "start": "...", "build": "...", "climax": "...", "resolve": "..." },
    "key_nodes": [ { "name": "初遇", "description": "...", "trigger": "开场" }, ... ],
    "endings": { "good": "...", "neutral": "...", "bad": "...", "secret": "..." }
  }
}
```

### 11.4 剧本种子文件分布

| 文件 | 数量 | 主题 |
|------|------|------|
| `ancient.json` | 15 | 古代宫廷/江湖 |
| `angst.json` | 10 | 虐恋/悲伤 |
| `comedy.json` | 15 | 喜剧/搞笑 |
| `dark.json` | 15 | 暗黑/病娇 |
| `ethical.json` | 10 | 伦理/禁忌 |
| `fantasy.json` | 10 | 仙侠/异世界 |
| `future.json` | 10 | 科幻/赛博朋克 |
| `harem.json` | 5 | 后宫 |
| `healing.json` | 15 | 治愈 |
| `rebirth.json` | 15 | 重生 |
| `republic.json` | 5 | 民国 |
| `revenge.json` | 5 | 复仇 |
| `suspense.json` | 5 | 悬疑 |
| `sweet.json` | 10 | 甜宠 |
| **总计** | **145** | |

### 11.5 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/script-library` | GET | 列表查询，支持多维度筛选 |
| `/api/script-library/random` | GET | 获取随机剧本 |
| `/api/script-library/tags` | GET | 获取所有分类标签 |
| `/api/script-library/tags/{category}` | GET | 获取指定维度的标签 |
| `/api/script-library/{id}` | GET | 获取剧本详情 |
| `/api/script-library` | POST | 创建剧本（需管理员权限） |
| `/api/script-library/{id}` | PUT | 更新剧本 |
| `/api/script-library/{id}` | DELETE | 删除剧本 |

### 11.6 关键文件

| 组件 | 路径 |
|------|------|
| 数据库迁移 | `backend/app/migrations/add_script_library_tables.py` |
| 数据导入 | `backend/app/migrations/import_script_library_data.py` |
| 数据模型 | `backend/app/models/script_library.py` |
| 服务层 | `backend/app/services/script_library_service.py` |
| API 路由 | `backend/app/routers/script_library.py` |
| 标签配置 | `config/script_tags.json` |
| 剧本种子 | `config/script_seeds/*.json` |
| 前端类型 | `frontend/src/types/scriptLibrary.ts` |
| 前端服务 | `frontend/src/services/scriptLibraryService.ts` |
| 前端页面 | `frontend/src/pages/ScriptLibrary/` |

---

## 总结

剧本系统创造沉浸式、AI 主导的叙事体验：

1. **角色主导** - AI 通过自然对话主动推进故事
2. **关系重要** - 亲密度和信任度自然解锁剧情阶段
3. **节点指导 AI** - 剧本节点提供上下文，而非用户界面
4. **进度追踪** - 会话状态和关系值持久保存
5. **多样结局** - 多种结局基于关系旅程
6. **剧本库** - 145+ 预定义剧本模板，9 维度分类

此设计优先考虑 **沉浸感和情感投入**，而非游戏式机制，让用户感觉在与角色共度一段故事，而非走过预设分支。