# 角色创建系统技术文档

## 概述

Roxy 官方角色创建系统支持三种创建模式：批量AI生成、模板变体、手动创建。系统集成了 LLM 生成角色档案、Novita/FAL 生成图片、R2 云存储、SEO 优化等功能。

---

## 创建模式

### 1. 批量AI生成

```
管理员配置参数（数量、分类、年龄范围） → 调用 LLM 生成角色档案
→ MediaService 生成头像和封面 → StorageService 上传到 R2
→ 生成 SEO 内容 → 保存到数据库
```

**端点**: `POST /admin/api/characters/batch-generate`

**请求体**:
```json
{
  "count": 5,
  "top_category": "girls",
  "personality_preferences": ["sweet", "romantic", "playful"],
  "age_min": 20,
  "age_max": 30,
  "generate_images": true,
  "optimize_seo": true
}
```

**响应**:
```json
{
  "success": true,
  "created_count": 5,
  "characters": [
    {
      "id": "char_abc123",
      "name": "Emma",
      "slug": "emma-abc123",
      "avatar_url": "https://r2.roxy.ai/characters/avatars/xxx.jpg",
      "cover_url": "https://r2.roxy.ai/characters/covers/xxx.jpg"
    }
  ]
}
```

### 2. 模板变体生成

```
选择预设模板 → 基于模板生成随机变体
→ 自动填充名字、年龄、性格、开场白等
→ 生成图片并上传 → 保存到数据库
```

**端点**: `POST /admin/api/characters/from-template`

**请求体**:
```json
{
  "template_id": "college_student",
  "variations": 3,
  "generate_images": true,
  "optimize_seo": true
}
```

### 3. 手动创建

```
管理员填写表单 → 提交角色信息 → 保存到数据库
→ 可选择是否自动生成图片
```

**端点**: `POST /admin/api/characters`

**请求体**:
```json
{
  "name": "Sophie",
  "first_name": "Sophie",
  "age": 25,
  "top_category": "girls",
  "description": "A sweet and caring girlfriend",
  "personality_tags": ["sweet", "caring", "romantic"],
  "greeting": "Hi, I'm Sophie! Nice to meet you~",
  "generate_images": false
}
```

---

## 数据模型

### Character 表结构

**文件**: `backend/app/models/character.py`

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | String(50) | 主键，格式 `char_xxxxxxxxxxxx` |
| `name` | String(100) | 角色名称 |
| `first_name` | String(50) | 显示用名 |
| `slug` | String(150) | URL友好标识（唯一） |
| `age` | Integer | 年龄（18-99） |
| `gender` | String(20) | 性别，默认 'female' |
| `top_category` | String(30) | 顶级分类：girls/anime/guys |
| `personality_tags` | JSON | 性格标签数组 |
| `personality_summary` | Text | 性格简介（卡片展示用） |
| `backstory` | Text | 背景故事 |
| `greeting` | Text | 开场白 |
| `system_prompt` | Text | 系统提示词 |
| `avatar_url` | String(512) | 头像 URL（R2） |
| `cover_url` | String(512) | 封面图 URL（R2） |
| `voice_id` | String(100) | 语音 ID |
| `meta_title` | String(200) | SEO 标题 |
| `meta_description` | Text | SEO 描述 |
| `keywords` | JSON | SEO 关键词数组 |
| `is_official` | Boolean | 是否官方角色 |
| `is_public` | Boolean | 是否公开 |
| `template_id` | String(50) | 来源模板 ID |
| `generation_mode` | String(20) | 创建模式：batch/manual/template |
| `popularity_score` | Float | 人气分数 |
| `chat_count` | Integer | 对话次数 |
| `view_count` | Integer | 浏览次数 |

### 索引

```sql
CREATE INDEX idx_characters_slug ON characters(slug);
CREATE INDEX idx_characters_top_category ON characters(top_category);
CREATE INDEX idx_characters_is_official ON characters(is_official);
CREATE INDEX idx_characters_is_public ON characters(is_public);
CREATE INDEX idx_characters_popularity ON characters(popularity_score DESC);
```

---

## 预设模板

**文件**: `backend/app/models/character.py` (CHARACTER_TEMPLATES)

| 模板ID | 名称 | 年龄范围 | 性格特征 |
|--------|------|----------|----------|
| `college_student` | 女大学生 | 19-23 | playful, smart, romantic, shy |
| `office_lady` | 职场白领 | 25-32 | mature, independent, confident |
| `girl_next_door` | 邻家女孩 | 20-26 | sweet, kind, friendly, caring |
| `romantic_artist` | 艺术女生 | 22-28 | creative, passionate, mysterious |
| `fitness_coach` | 健身教练 | 24-30 | energetic, motivating, confident |
| `mystic_witch` | 神秘女巫 | 20-99 | mysterious, wise, enchanting |
| `sweet_barista` | 甜美咖啡师 | 21-27 | friendly, warm, chatty |
| `boss_lady` | 霸道女总裁 | 28-38 | dominant, confident, ambitious |

---

## 服务层架构

### CharacterService

**文件**: `backend/app/services/character_service.py`

核心方法：

| 方法 | 说明 |
|------|------|
| `create_character(data)` | 创建单个角色 |
| `get_character_by_id(id)` | 通过 ID 获取角色 |
| `get_character_by_slug(slug)` | 通过 slug 获取角色（SEO友好） |
| `list_characters(filters, pagination)` | 分页列表查询 |
| `list_official_characters(category, filters)` | 官方角色列表（前台展示） |
| `discover_characters(category, filter_tag, search)` | 发现页接口 |
| `update_character(id, data)` | 更新角色 |
| `delete_character(id)` | 删除角色 |
| `batch_delete(ids)` | 批量删除 |
| `increment_chat_count(id)` | 增加对话计数 |
| `update_popularity_score(id, score)` | 更新人气分 |

### CharacterFactory

**文件**: `backend/app/services/character_factory.py`

核心方法：

| 方法 | 说明 |
|------|------|
| `generate_batch(count, config)` | 批量 AI 生成 |
| `generate_from_template(template_id, variations)` | 模板变体生成 |
| `generate_single_character(name, ...)` | 生成单个角色 |
| `regenerate_images(character_id)` | 重新生成图片 |
| `_generate_ai_profiles(count, ...)` | 调用 LLM 生成角色档案 |
| `_generate_character_images(profile)` | 生成头像和封面 |
| `_generate_seo_content(profile)` | 生成 SEO 内容 |

### StorageService

**文件**: `backend/app/services/storage_service.py`

核心方法：

| 方法 | 说明 |
|------|------|
| `upload_from_url(source_url, folder, filename)` | 从 URL 下载并上传到 R2 |
| `upload_bytes(content, folder, filename)` | 上传二进制数据到 R2 |

---

## 图片生成流程

```
CharacterFactory._generate_character_images(profile)
    │
    ├── 构建 Prompt
    │   avatar_prompt = "portrait photo of {age}-year-old woman named {name}, 
    │                    {personality} personality, professional photography..."
    │   cover_prompt = "full body photo of {age}-year-old woman, {personality}..."
    │
    ├── 调用 MediaService.generate_image()
    │   └── NovitaImageProvider 或 FALImageProvider
    │       └── 返回临时图片 URL
    │
    ├── 上传到 R2
    │   └── StorageService.upload_from_url()
    │       └── 返回 CDN URL (https://r2.roxy.ai/characters/avatars/xxx.jpg)
    │
    └── 返回图片 URL
        {
          "avatar_url": "https://r2.roxy.ai/...",
          "cover_url": "https://r2.roxy.ai/...",
          "avatar_card_url": "https://r2.roxy.ai/..."
        }
```

---

## LLM 角色档案生成

**Prompt 模板**:

```
Generate a detailed character profile for an AI companion app character.

Character Name: {name}
Age: {age}
Category: {top_category}
Personality Traits: {personality_tags}

Generate a JSON object with these fields:
- description: A 1-2 sentence description of the character (max 200 chars)
- personality_summary: A short personality summary (max 100 chars)
- backstory: A brief backstory (max 300 chars)
- greeting: A friendly opening message the character would say (max 150 chars)

Respond with valid JSON only.
```

**回退策略**: LLM 调用失败时使用默认值：

```python
{
    "description": f"A {age}-year-old {' '.join(personality_tags[:2])} woman.",
    "personality_summary": f"{' and '.join(personality_tags[:2])}.",
    "backstory": "",
    "greeting": f"Hi, I'm {name}! Nice to meet you!",
}
```

---

## SEO 优化

### Slug 生成规则

```python
def generate_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)      # 移除特殊字符
    slug = re.sub(r'[\s_-]+', '-', slug)      # 空格和下划线转为连字符
    slug = re.sub(r'^-+|-+$', '', slug)       # 移除首尾连字符
    return slug or f"character-{uuid.uuid4().hex[:6]}"
```

**冲突处理**: 若 slug 已存在，追加 `{slug}-{character_id[-6:]}`

### SEO 内容生成

```python
{
    "slug": generate_slug(name),
    "meta_title": f"{name} - AI Character | RoxyClub",
    "meta_description": description[:160],
    "keywords": personality_tags + [name, "AI character", "virtual companion"],
    "seo_optimized": True
}
```

---

## API 端点汇总

### 管理端 API

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/admin/api/characters` | 创建角色 |
| POST | `/admin/api/characters/batch-generate` | 批量 AI 生成 |
| POST | `/admin/api/characters/from-template` | 模板变体生成 |
| GET | `/admin/api/characters` | 角色列表（分页） |
| GET | `/admin/api/characters/{id}` | 角色详情 |
| PUT | `/admin/api/characters/{id}` | 更新角色 |
| DELETE | `/admin/api/characters/{id}` | 删除角色 |
| POST | `/admin/api/characters/batch-delete` | 批量删除 |
| POST | `/admin/api/characters/{id}/regenerate-images` | 重新生成图片 |
| GET | `/admin/api/character-templates` | 模板列表 |

### 前台展示 API

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/characters/official` | 官方角色列表 |
| GET | `/api/characters/official/{id}` | 官方角色详情 |
| GET | `/api/characters/discover` | 发现页（分页/搜索/筛选） |
| GET | `/api/characters/by-slug/{slug}` | SEO 友好详情页 |
| GET | `/api/characters/categories` | 分类列表（含筛选标签） |

---

## 前端管理页面

### 角色创建页

**文件**: `frontend/src/pages/admin/CharacterCreatePage.tsx`

**路由**: `/admin/characters/create`

**功能**:
- 三种创建模式切换（批量/模板/手动）
- 批量生成配置：数量、分类、年龄范围、性格偏好
- 模板选择：下拉选择预设模板
- 手动创建：完整表单填写

### 角色编辑页

**文件**: `frontend/src/pages/admin/CharacterEditPage.tsx`

**路由**: `/admin/characters/{id}/edit`

**功能**:
- 基本信息、性格描述、背景故事编辑
- SEO 设置
- 图片预览和重新生成
- 状态管理（active/draft/archived）
- 统计数据展示

### 角色列表页

**文件**: `frontend/src/pages/admin/tabs/CharactersTab.tsx`

**功能**:
- 分页列表、搜索、筛选
- 批量选择、批量删除
- AI 填充、编辑、删除操作
- 状态、分类、人气显示

---

## 配置项

### 后端环境变量

```env
# R2 存储
R2_ACCESS_KEY_ID=your_r2_access_key
R2_SECRET_ACCESS_KEY=your_r2_secret_key
R2_BUCKET_NAME=aigirl-media
R2_ENDPOINT_URL=https://xxx.r2.cloudflarestorage.com
R2_PUBLIC_URL=https://r2.roxy.ai

# 图片生成
NOVITA_API_KEY=your_novita_api_key
NOVITA_BASE_URL=https://api.novita.ai
FAL_API_KEY=your_fal_api_key

# LLM
LLM_API_KEY=your_llm_api_key
LLM_PROVIDER=novita
LLM_PRIMARY_MODEL=meta-llama/llama-3.3-70b-instruct
```

---

## 关键文件清单

### 后端

| 文件 | 说明 |
|------|------|
| `app/models/character.py` | Character 模型、Schema、模板定义 |
| `app/services/character_service.py` | 角色 CRUD 服务 |
| `app/services/character_factory.py` | AI 批量生成服务 |
| `app/services/storage_service.py` | R2 云存储服务 |
| `app/routers/admin.py` | 管理端 API |
| `app/routers/character.py` | 前台展示 API |
| `app/core/database.py` | 数据库表定义 |

### 前端

| 文件 | 说明 |
|------|------|
| `src/pages/admin/CharacterCreatePage.tsx` | 角色创建页 |
| `src/pages/admin/CharacterEditPage.tsx` | 角色编辑页 |
| `src/pages/admin/tabs/CharactersTab.tsx` | 角色列表 Tab |
| `src/types/character-templates.ts` | 模板类型定义 |

---

## 注意事项

1. **图片生成耗时**: 每个角色图片生成约需 10-30 秒，批量生成时请控制数量
2. **R2 配置**: 确保 R2 公开 URL 配置正确，否则图片无法访问
3. **LLM 回退**: LLM 调用失败时使用默认值，不会中断流程
4. **Slug 唯一性**: 自动处理 slug 冲突，追加 ID 后缀
5. **SEO 限制**: meta_description 最多 160 字符，超出自动截断
