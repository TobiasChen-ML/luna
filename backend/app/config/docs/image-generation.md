# 图片生成模块文档

## 目录

1. [架构概览](#架构概览)
2. [API 端点](#api-端点)
3. [Novita Provider 实现](#novita-provider-实现)
4. [LoRA 配置](#lora-配置)
5. [IP-Adapter 换脸](#ip-adapter-换脸)
6. [ControlNet Pose 参考](#controlnet-pose-参考)
7. [任务状态管理](#任务状态管理)
8. [回调处理](#回调处理)
9. [前端集成](#前端集成)
10. [环境配置](#环境配置)
11. [调试指南](#调试指南)

---

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌──────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │  ChatPage    │  │ GenerateImage   │  │   ChatInput       │  │
│  │  Shoot Photo │  │ ComposerPage    │  │   Shoot Photo     │  │
│  └──────┬───────┘  └────────┬─────────┘  └─────────┬─────────┘  │
│         │                   │                      │            │
│         └───────────────────┼──────────────────────┘            │
│                             │                                    │
│                    api.post('/images/generate-mature-lora')      │
│                             │                                    │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                        Backend (FastAPI)                         │
│                             │                                    │
│  ┌──────────────────────────┼───────────────────────────────┐   │
│  │              routers/media.py                              │   │
│  │  /images/generate-mature-lora                              │   │
│  │  /images/generate-pose-mature                              │   │
│  │  /images/generate-with-face                               │   │
│  │  /images/tasks/{task_id}                                   │   │
│  │  /images/callbacks/novita                                  │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────┼───────────────────────────────┐   │
│  │              MediaService                                  │   │
│  │  - get_image_provider("novita")                           │   │
│  │  - get_video_provider("novita")                           │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
│  ┌──────────────────────────┼───────────────────────────────┐   │
│  │           NovitaImageProvider                             │   │
│  │  - txt2img_async()     → task_id                          │   │
│  │  - img2img_async()     → task_id (支持 LoRA/IP-Adapter)   │   │
│  │  - generate_with_ip_adapter() → task_id (换脸)            │   │
│  │  - get_task_result()  → TaskResult                        │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                    │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              │ HTTP POST/GET
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                     Novita API                                   │
│                                                                  │
│  Base URL: https://api.novita.ai/v3                              │
│                                                                  │
│  端点:                                                           │
│  - POST /async/txt2img       → 异步文生图                       │
│  - POST /async/img2img       → 异步图生图                       │
│  - GET  /async/task-result   → 查询任务状态                     │
│                                                                  │
│  回调 (Webhook):                                                 │
│  - POST /images/callbacks/novita                                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## API 端点

### 1. POST `/api/images/generate-mature-lora`

**用途**: 图生图 + LoRA 风格

**请求体**:
```json
{
  "prompt": "beautiful woman, seductive pose",
  "character_id": "char_001",
  "session_id": "session_001",
  "lora_id": "blowjob",
  "width": 1024,
  "height": 1024,
  "steps": 20,
  "guidance_scale": 7.5,
  "strength": 0.75,
  "negative_prompt": "optional negative prompt"
}
```

**响应**:
```json
{
  "task_id": "f10333f2-2dd7-4f56-a177-e3c02a774d9a",
  "status": "TASK_STATUS_QUEUED",
  "character_id": "char_001",
  "session_id": "session_001"
}
```

**流程**:
1. 前端发送 prompt + lora_id
2. 后端从配置获取 LoRA trigger_word
3. 拼接 prompt: `"{trigger_word}, {prompt}"`
4. 调用 `provider.txt2img_async()`
5. 返回 task_id，前端轮询或等待 SSE

---

### 2. POST `/api/images/generate-pose-mature`

**用途**: 基于 pose 参考图生成

**请求体**:
```json
{
  "prompt": "beautiful woman, same pose",
  "character_id": "char_001",
  "session_id": "session_001",
  "pose_image_url": "https://example.com/pose.jpg",
  "width": 1024,
  "height": 1024,
  "controlnet_strength": 0.7
}
```

**流程**:
1. 下载 pose 参考图并转 base64
2. 创建 ControlNet 配置:
   ```python
   ControlNetConfig(
       model_name="control_v11p_sd15_openpose",
       image_base64=pose_image_base64,
       strength=0.7,
       preprocessor="openpose"
   )
   ```
3. 调用 `provider.img2img_async(controlnet=controlnet)`

---

### 3. POST `/api/images/generate-with-face`

**用途**: IP-Adapter 换脸生成

**请求体**:
```json
{
  "prompt": "beautiful woman, smiling",
  "face_image_url": "https://example.com/face.jpg",
  "character_id": "char_001",
  "width": 512,
  "height": 768,
  "ip_adapter_strength": 0.8
}
```

**流程**:
1. 下载脸部参考图
2. 使用 IP-Adapter 保持面部一致性
3. 调用 `provider.generate_with_ip_adapter()`

---

### 4. GET `/api/images/tasks/{task_id}`

**用途**: 查询任务状态

**响应**:
```json
{
  "task_id": "f10333f2-2dd7-4f56-a177-e3c02a774d9a",
  "status": "TASK_STATUS_SUCCEED",
  "progress": 100,
  "image_url": "https://faas-output-image.s3.amazonaws.com/...",
  "error": null
}
```

**状态值**:
- `TASK_STATUS_QUEUED` - 排队中
- `TASK_STATUS_PROCESSING` - 处理中
- `TASK_STATUS_SUCCEED` - 成功
- `TASK_STATUS_FAILED` - 失败

---

### 5. POST `/api/images/callbacks/novita`

**用途**: Novita 任务完成回调

**请求体 (来自 Novita)**:
```json
{
  "task_id": "f10333f2-2dd7-4f56-a177-e3c02a774d9a",
  "task": {
    "status": "TASK_STATUS_SUCCEED",
    "task_type": "TXT_TO_IMG"
  },
  "images": [
    {
      "image_url": "https://...",
      "image_type": "jpeg"
    }
  ]
}
```

**处理逻辑**:
1. 检查 `task.status`
2. 若成功，通过 Redis Pub/Sub 广播 `image_done` 事件
3. 若失败，广播 `image_failed` 事件

---

## Novita Provider 实现

### 文件位置
`backend/app/services/media/__init__.py`

### 核心类和方法

#### NovitaImageProvider

```python
class NovitaImageProvider(BaseMediaProvider):
    DEFAULT_MODEL = "juggernautXL_juggXIByRundiffusion_148819.safetensors"
    DEFAULT_MODEL_SD15 = "realisticVisionV51_v51VAE_94301.safetensors"
    
    # 异步文生图
    async def txt2img_async(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        model: Optional[str] = None,
        steps: int = 20,
        guidance_scale: float = 7.5,
        seed: int = -1,
        loras: Optional[list[LoRAConfig]] = None,
        restore_faces: bool = False,
    ) -> str:
        """返回 task_id"""
    
    # 异步图生图 (支持 LoRA/IP-Adapter/ControlNet)
    async def img2img_async(
        self,
        init_image_url: str,
        prompt: str,
        negative_prompt: Optional[str] = None,
        strength: float = 0.7,
        loras: Optional[list[LoRAConfig]] = None,
        ip_adapters: Optional[list[IPAdapterConfig]] = None,
        controlnet: Optional[ControlNetConfig] = None,
    ) -> str:
        """返回 task_id"""
    
    # IP-Adapter 换脸
    async def generate_with_ip_adapter(
        self,
        prompt: str,
        face_image_url: str,
        ip_adapter_strength: float = 0.8,
    ) -> str:
        """返回 task_id"""
    
    # 查询任务状态
    async def get_task_result(self, task_id: str) -> TaskResult:
        """返回任务状态"""
    
    # 等待任务完成
    async def wait_for_task(
        self,
        task_id: str,
        timeout_seconds: int = 300,
        poll_interval: float = 2.0,
    ) -> TaskResult:
        """轮询直到完成或超时"""
    
    # 辅助方法：下载图片转 base64
    async def _download_image_base64(self, image_url: str) -> str:
        """下载图片并返回 base64 编码"""
```

#### 数据类

```python
@dataclass
class ImageGenerationResult:
    image_url: str
    seed: Optional[int] = None
    width: int = 512
    height: int = 512
    task_id: Optional[str] = None

@dataclass
class TaskResult:
    task_id: str
    status: str
    progress: float = 0.0
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    error: Optional[str] = None
    seed: Optional[int] = None

@dataclass
class LoRAConfig:
    model_name: str
    strength: float = 0.7

@dataclass
class IPAdapterConfig:
    image_base64: str
    strength: float = 0.8
    model_name: str = "ip-adapter_sd15.bin"

@dataclass
class ControlNetConfig:
    model_name: str
    image_base64: str
    strength: float = 1.0
    preprocessor: Optional[str] = None
```

### Novita API 请求示例

#### txt2img 请求体
```json
{
  "extra": {
    "response_image_type": "jpeg"
  },
  "request": {
    "model_name": "juggernautXL_juggXIByRundiffusion_148819.safetensors",
    "prompt": "beautiful woman, seductive pose",
    "negative_prompt": "low quality, bad anatomy...",
    "width": 1024,
    "height": 1024,
    "image_num": 1,
    "steps": 20,
    "seed": -1,
    "guidance_scale": 7.5,
    "sampler_name": "DPM++ 2M",
    "clip_skip": 1,
    "restore_faces": true,
    "loras": [
      {"model_name": "add_detail_44319", "strength": 0.7}
    ]
  }
}
```

#### img2img 请求体 (带 IP-Adapter)
```json
{
  "extra": {"response_image_type": "jpeg"},
  "request": {
    "model_name": "realisticVisionV51_v51VAE_94301.safetensors",
    "image_base64": "<base64_encoded_image>",
    "prompt": "beautiful woman",
    "width": 1024,
    "height": 1024,
    "image_num": 1,
    "steps": 20,
    "guidance_scale": 7.5,
    "sampler_name": "DPM++ 2M",
    "strength": 0.7,
    "ip_adapters": [
      {
        "model_name": "ip-adapter_sd15.bin",
        "image_base64": "<face_image_base64>",
        "strength": 0.8
      }
    ]
  }
}
```

#### img2img 请求体 (带 ControlNet)
```json
{
  "extra": {"response_image_type": "jpeg"},
  "request": {
    "model_name": "juggernautXL_juggXIByRundiffusion_148819.safetensors",
    "image_base64": "<base64_encoded_image>",
    "prompt": "same pose, different outfit",
    "width": 1024,
    "height": 1024,
    "image_num": 1,
    "steps": 20,
    "guidance_scale": 7.0,
    "sampler_name": "DPM++ 2M",
    "strength": 1.0,
    "controlnet": {
      "units": [
        {
          "model_name": "control_v11p_sd15_openpose",
          "image_base64": "<pose_image_base64>",
          "strength": 0.7,
          "preprocessor": "openpose"
        }
      ]
    }
  }
}
```

---

## LoRA 配置

### 文件位置
`backend/app/config/lora_configs.py`

### 配置结构

```python
@dataclass
class LoRAConfig:
    id: str                    # LoRA ID (前端使用)
    name: str                  # 显示名称
    trigger_word: str          # 触发词 (自动拼接到 prompt 前面)
    description: str           # 描述
    default_strength: float    # 默认强度
    novita_model_name: Optional[str]  # Novita API 中的模型名
```

### 当前可用 LoRA

| ID | 名称 | Description |
|----|------|-------------|
| blowjob | Blowjob | Oral sex POV |
| butterfly_sex | Butterfly Sex | Missionary position |
| cumshot | Cumshot | Facial finish |
| doggy_style | Doggy Style | Doggy style position |
| fivesome | Fivesome | Group sex |
| foodtease | Food Tease | Sensual food play |
| foursome | Foursome | Group sex |
| handjob | Handjob | POV handjob |
| licking_cock | Licking Cock | Oral teasing |
| orgasming | Orgasming | Orgasm expression |
| reverse_gang_bang | Reverse Gang Bang | Multiple women |
| reversecowgirl | Reverse Cowgirl | Reverse cowgirl position |
| riding_cowgirl | Riding Cowgirl | Cowgirl position |
| self_stroking | Self Stroking | Masturbation |
| sidefuck | Sidefuck | Side-lying position |
| teasing | Teasing | Seductive pose |
| threesome | Threesome | Threesome sex |
| titty_fucking | Titty Fucking | Paizuri |
| undressing | Undressing | Strip tease |

### 使用示例

```python
from app.config import get_lora_config, get_lora_trigger_word

# 获取配置
config = get_lora_config("blowjob")
# config.trigger_word = "blowjob, oral sex, penis in mouth, pov, ..."

# 构建 prompt
prompt = f"{config.trigger_word}, {user_prompt}"

# 获取强度
strength = config.default_strength  # 0.95
```

### 注意事项

⚠️ **当前 `novita_model_name=None`**

需要从 Novita API 获取实际可用的 LoRA 模型名:
```bash
curl 'https://api.novita.ai/v3/model?filter.types=lora' \
  -H 'Authorization: Bearer YOUR_API_KEY'
```

查找响应中的 `sd_name_in_api` 字段，更新到配置中。

---

## IP-Adapter 换脸

### 工作原理

IP-Adapter (Image Prompt Adapter) 允许使用图片作为提示，保持面部或风格的一致性。

### 流程图

```
┌──────────────┐     ┌───────────────┐     ┌────────────────┐
│  用户上传    │     │  提取脸部特征  │     │   IP-Adapter   │
│  脸部照片    │ ──▶ │  转 base64    │ ──▶ │   注入生成     │
└──────────────┘     └───────────────┘     └────────────────┘
                                                   │
                                                   ▼
                                           ┌────────────────┐
                                           │   生成的新图    │
                                           │   保留脸部特征  │
                                           └────────────────┘
```

### Novita API 参数

```json
{
  "ip_adapters": [
    {
      "model_name": "ip-adapter_sd15.bin",      // SD 1.5 模型
      // "model_name": "ip-adapter_sdxl.bin",  // SDXL 模型
      "image_base64": "<face_image_base64>",
      "strength": 0.8    // 0-1, 越高越像原图
    }
  ]
}
```

### 代码实现

```python
async def generate_with_ip_adapter(
    self,
    prompt: str,
    face_image_url: str,
    ip_adapter_strength: float = 0.8,
) -> str:
    # 下载并编码脸部图片
    face_base64 = await self._download_image_base64(face_image_url)
    
    # 构建请求
    payload = {
        "request": {
            "model_name": self.DEFAULT_MODEL_SD15,  # SD 1.5
            "prompt": prompt,
            "ip_adapters": [{
                "model_name": "ip-adapter_sd15.bin",
                "image_base64": face_base64,
                "strength": ip_adapter_strength,
            }],
            # ...
        }
    }
    
    # 提交任务
    return task_id
```

### 强度建议

| strength | 效果 |
|----------|------|
| 0.5-0.6 | 轻微相似，更多创意发挥 |
| 0.7-0.8 | 平衡相似度和创意 |
| 0.9-1.0 | 高度相似，可能过度拟合 |

---

## ControlNet Pose 参考

### 工作原理

ControlNet 允许通过 pose 参考图控制生成人物的姿势。

### 流程图

```
┌──────────────┐     ┌───────────────┐     ┌────────────────┐
│  Pose 参考   │     │  OpenPose    │     │   ControlNet   │
│  图片        │ ──▶ │  提取骨架     │ ──▶ │   引导生成     │
└──────────────┘     └───────────────┘     └────────────────┘
                                                   │
                                                   ▼
                                           ┌────────────────┐
                                           │   生成的图以    │
                                           │   相同姿势呈现  │
                                           └────────────────┘
```

### Novita API 参数

```json
{
  "controlnet": {
    "units": [
      {
        "model_name": "control_v11p_sd15_openpose",
        "image_base64": "<pose_image_base64>",
        "strength": 0.7,
        "preprocessor": "openpose"
      }
    ]
  }
}
```

### 可用 ControlNet 模型

| model_name | 用途 |
|------------|------|
| control_v11p_sd15_openpose | 姿势检测 |
| control_v11p_sd15_canny | 边缘检测 |
| control_v11p_sd15_depth | 深度图 |
| control_v11p_sd15_scribble | 涂鸦 |
| control_v11f1e_sd15_tile | 细节增强 |

### 预处理器选项

| preprocessor | 说明 |
|--------------|------|
| openpose | 提取人体骨架 |
| openpose_face | 骨架 + 面部关键点 |
| openpose_full | 完整人体关键点 |
| depth_midas | 深度估计 |
| canny | 边缘检测 |

### 代码实现

```python
controlnet = ControlNetConfig(
    model_name="control_v11p_sd15_openpose",
    image_base64=pose_image_base64,
    strength=0.7,          # 姿势控制强度
    preprocessor="openpose"
)

task_id = await provider.img2img_async(
    init_image_url=init_image_url,  # 或 pose_image_url
    prompt=prompt,
    controlnet=controlnet,
)
```

---

## 任务状态管理

### 状态流转

```
TASK_STATUS_QUEUED ──▶ TASK_STATUS_PROCESSING ──▶ TASK_STATUS_SUCCEED
        │                      │
        │                      └──▶ TASK_STATUS_FAILED
        │
        └──▶ (超时)
```

### 轮询机制

前端实现双重机制：
1. **SSE 监听** (主要): 订阅 `image_done` / `image_failed` 事件
2. **HTTP 轮询** (备份): 每 5 秒查询一次 `/images/tasks/{task_id}`

```typescript
const unsubDone = notificationService.on('image_done', (data) => {
  if (data.message_id !== task_id) return;
  // 处理完成的图片
  updateMessage({ image_url: data.image_url });
});

// 备用轮询
const pollInterval = setInterval(async () => {
  const res = await api.get(`/images/tasks/${task_id}`);
  if (res.data.status === 'TASK_STATUS_SUCCEED') {
    // 处理完成
  }
}, 5000);
```

### 超时处理

- 前端超时: 6 分钟 (`360_000 ms`)
- 后端等待超时: 5 分钟 (`300 seconds`)

```typescript
const TIMEOUT_MS = 360_000;
const timeoutId = setTimeout(() => {
  updateMessage({ content: 'Image generation timed out.' });
}, TIMEOUT_MS);
```

---

## 回调处理

### Novita Webhook 配置

在请求中配置 webhook:

```python
payload = {
  "extra": {
    "webhook": {
      "url": "https://your-domain.com/api/images/callbacks/novita"
    }
  },
  "request": { ... }
}
```

### 回调处理逻辑

```python
@router.post("/callbacks/novita")
async def novita_callback(request: Request) -> BaseResponse:
    body = await request.json()
    
    task_id = body.get("task_id")
    task = body.get("task", {})
    status = task.get("status")
    images = body.get("images", [])
    
    if task_id:
        if status == "TASK_STATUS_SUCCEED" and images:
            image_url = images[0].get("image_url")
            # 通过 Redis Pub/Sub 广播
            await redis_client.publish(
                "image_done",
                json.dumps({
                    "message_id": task_id,
                    "image_url": image_url,
                    "task_id": task_id,
                })
            )
        
        elif status == "TASK_STATUS_FAILED":
            error = task.get("reason", "Unknown error")
            await redis_client.publish(
                "image_failed",
                json.dumps({
                    "task_id": task_id,
                    "error": error,
                })
            )
    
    return BaseResponse(success=True)
```

### Redis Pub/Sub 事件

| Channel | 数据 | 说明 |
|---------|------|------|
| `image_done` | `{message_id, image_url, task_id}` | 图片生成成功 |
| `image_failed` | `{task_id, error}` | 图片生成失败 |
| `video_completed` | `{task_id, video_url}` | 视频生成成功 |

---

## 前端集成

### ChatPage 生图流程

```typescript
const handleGenerateImage = async (
  prompt: string,
  poseImageUrl?: string,
  loraId?: string
) => {
  const endpoint = poseImageUrl
    ? '/images/generate-pose-mature'
    : '/images/generate-mature-lora';

  const response = await api.post(endpoint, {
    prompt,
    character_id: currentCharacter.id,
    session_id: sessionId,
    pose_image_url: poseImageUrl,
    lora_id: loraId,
  });

  const { task_id } = response.data;

  // SSE 监听
  const unsubDone = notificationService.on('image_done', (data) => {
    if (data.message_id !== task_id) return;
    updateMessage({
      content: '',
      image_url: data.image_url,
    });
  });

  // 轮询备份
  const pollInterval = setInterval(async () => {
    const res = await api.get(`/images/tasks/${task_id}`);
    if (res.data.status === 'TASK_STATUS_SUCCEED') {
      updateMessage({
        content: '',
        image_url: res.data.image_url,
      });
    }
  }, 5000);
};
```

### ChatInput 组件

```typescript
// Shoot Photo 按钮
<Button onClick={toggleImagePrompt}>
  <Camera size={12} />
  Shoot Photo
</Button>

// LoRA 选择器
<ImageLoraSelector
  selectedId={selectedImageLora?.id}
  onSelect={handleImageLoraSelect}
/>

// 发送生图请求
await onGenerateImage(
  imagePrompt.trim(),
  selectedPose?.thumbnailUrl,
  selectedImageLora?.id,
);
```

### GenerateImageComposerPage

```typescript
const generateImages = async () => {
  const selectedPose = POSE_PRESETS.find(p => p.id === selectedPoseId);
  
  const taskResponses = await Promise.all(
    Array.from({ length: numImages }, () => {
      if (selectedPose?.thumbnailUrl) {
        return api.post('/images/generate-pose-mature', {
          prompt,
          character_id: characterId,
          pose_image_url: selectedPose.thumbnailUrl,
        });
      }
      return api.post('/images/generate-mature-lora', {
        prompt,
        character_id: characterId,
        lora_id: selectedImageLora?.id,
      });
    })
  );
  
  // 等待所有任务完成
  const urls = await Promise.allSettled(
    taskIds.map(waitForImage)
  );
  
  setGeneratedImages(urls);
};
```

---

## 环境配置

### 必需环境变量

```env
# Novita API
NOVITA_API_KEY=nv-xxxxxxxxxxxxx
NOVITA_BASE_URL=https://api.novita.ai/v3

# Redis (用于 Pub/Sub)
REDIS_URL=redis://localhost:6379/0
```

### 可选配置

```env
# FAL.ai (备用 provider)
FAL_API_KEY=xxxxxxxxx

# 图片存储
R2_ACCOUNT_ID=xxxxx
R2_ACCESS_KEY_ID=xxxxx
R2_SECRET_ACCESS_KEY=xxxxx
R2_BUCKET_NAME=roxy-media
```

### 模型配置

可在代码中修改默认模型:

```python
DEFAULT_MODEL = "juggernautXL_juggXIByRundiffusion_148819.safetensors"  # SDXL
DEFAULT_MODEL_SD15 = "realisticVisionV51_v51VAE_94301.safetensors"       # SD 1.5
```

---

## 调试指南

### 1. 测试 API 连接

```bash
# 直接调用 Novita API
curl 'https://api.novita.ai/v3/async/txt2img' \
  -H 'Authorization: Bearer YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "request": {
      "model_name": "juggernautXL_juggXIByRundiffusion_148819.safetensors",
      "prompt": "a cute dog",
      "width": 512,
      "height": 512,
      "image_num": 1,
      "steps": 20,
      "guidance_scale": 7.5,
      "sampler_name": "DPM++ 2M"
    }
  }'
```

### 2. 查询可用模型

```bash
# 查询 checkpoints
curl 'https://api.novita.ai/v3/model?filter.types=checkpoint' \
  -H 'Authorization: Bearer YOUR_API_KEY'

# 查询 LoRA
curl 'https://api.novita.ai/v3/model?filter.types=lora' \
  -H 'Authorization: Bearer YOUR_API_KEY'
```

### 3. 查看任务状态

```bash
curl 'https://api.novita.ai/v3/async/task-result?task_id=TASK_ID' \
  -H 'Authorization: Bearer YOUR_API_KEY'
```

### 4. 本地测试端点

```bash
# 测试生图端点
curl -X POST 'http://localhost:8999/api/images/generate-mature-lora' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -d '{
    "prompt": "beautiful woman, smiling",
    "character_id": "test_char",
    "lora_id": "teasing"
  }'

# 查询任务状态
curl 'http://localhost:8999/api/images/tasks/TASK_ID' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### 5. 日志调试

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 关键日志点
logger.info(f"Submitting image generation: prompt={prompt}")
logger.info(f"Task submitted: task_id={task_id}")
logger.info(f"Task status: {result.status}")
```

### 6. 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 503 Provider not available | NOVITA_API_KEY 未配置 | 检查 .env 文件 |
| Task timeout | 任务排队时间过长 | 增加超时时间或检查 Novita 账户 |
| 图片未返回 | SSE 连接断开 | 使用 HTTP 轮询备份 |
| LoRA 无效 | model_name 错误 | 从 Novita API 查询正确名称 |
| IP-Adapter 无效 | 模型不匹配 | 用 SD 1.5 模型配 ip-adapter_sd15.bin |

---

## 附录

### Novita API 参考文档

- 官方文档: https://novita.ai/docs
- txt2img: https://novita.ai/docs/api-reference/model-apis-txt2img
- img2img: https://novita.ai/docs/api-reference/model-apis-img2img
- task-result: https://novita.ai/docs/api-reference/model-apis-task-result

### 相关文件清单

```
backend/
├── app/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── lora_configs.py          # LoRA 配置
│   │   └── docs/
│   │       └── image-generation.md  # 本文档
│   ├── routers/
│   │   └── media.py                 # 图片生成端点
│   └── services/
│       ├── media/
│       │   └── __init__.py           # Novita Provider
│       ├── media_service.py          # Media 服务
│       ├── llm_service.py            # LLM 服务 (含意图检测)
│       └── image_intent_handler.py   # 图片意图处理

frontend/
└── src/
    ├── pages/
    │   ├── ChatPage.tsx              # 聊天页面
    │   └── GenerateImageComposerPage.tsx
    ├── components/
    │   └── chat/
    │       └── ChatInput.tsx         # Shoot Photo UI
    └── config/
        └── imageGenerationLoras.ts  # 前端 LoRA 配置
```

---

*文档版本: 1.0.0*
*最后更新: 2026-04-15*
