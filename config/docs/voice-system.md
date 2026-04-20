# 语音系统技术文档

## 概述

Roxy 的语音系统基于 ElevenLabs TTS API，支持角色语音条播放和自动语音回复。系统包含语音配置、意图检测、TTS 生成、Credit 扣费等完整流程。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         用户消息                                 │
│              "Say goodnight to me"                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Intent Detection                            │
│           LLMService.detect_intent()                             │
│           → { intent: "audio", confidence: 0.85 }                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    检查角色 voice_id                             │
│           character.voice_id 存在?                               │
│           → 是: 继续 | 否: 跳过语音生成                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Credit 检查与扣费                           │
│           DatabaseService.deduct_credits_by_firebase_uid()       │
│           成功: 继续生成 | 失败: 发送 insufficient_credits 事件    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      文本回复生成                                 │
│           LLM 流式生成文本响应                                    │
│           → SSE: text_delta → text_done                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       TTS 生成                                   │
│           VoiceService.generate_tts()                            │
│           → ElevenLabs API                                       │
│           → SSE: voice_note_pending → voice_note_ready           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     前端语音条播放                                │
│           VoiceNotePlayer 组件                                   │
│           → 波形可视化、播放控制、进度显示                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 一、Voice ID 配置

### 1.1 数据库字段

**表**: `characters`

**字段**: `voice_id` (String(100), nullable)

存储 ElevenLabs 的 Voice ID，例如: `21m00Tcm4TlvDq8ikWAM`

### 1.2 后端模型

**文件**: `backend/app/models/character.py`

```python
class CharacterBase(BaseModel):
    # ... 其他字段
    voice_id: Optional[str] = None
```

### 1.3 前端配置界面

**文件**: `frontend/src/pages/admin/CharacterEditPage.tsx`

在管理后台的角色编辑页面，提供 Voice ID 输入框：

```tsx
<div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
  <h2 className="text-lg font-semibold mb-4">语音设置</h2>
  <div className="space-y-4">
    <div>
      <label className="block text-sm text-zinc-400 mb-2">ElevenLabs Voice ID</label>
      <input
        type="text"
        value={formData.voice_id || ''}
        onChange={(e) => setFormData({ ...formData, voice_id: e.target.value })}
        className="w-full px-4 py-2 bg-zinc-800 border border-zinc-700 rounded-lg"
        placeholder="e.g., 21m00Tcm4TlvDq8ikWAM"
      />
      <p className="text-xs text-zinc-500 mt-1">
        Get Voice ID from ElevenLabs dashboard
      </p>
    </div>
  </div>
</div>
```

### 1.4 获取 ElevenLabs Voice ID

1. 登录 [ElevenLabs Dashboard](https://elevenlabs.io/app/voice-library)
2. 进入 Voice Library 或 VoiceLab
3. 选择或创建一个语音
4. 复制 Voice ID（格式类似：`21m00Tcm4TlvDq8ikWAM`）

---

## 二、Intent 检测

### 2.1 Intent 类型定义

**文件**: `backend/app/core/events.py`

```python
class IntentType(str, Enum):
    CHAT = "chat"        # 普通对话
    IMAGE = "image"      # 图片生成请求
    VIDEO = "video"      # 视频生成请求
    AUDIO = "audio"      # 语音回复请求
    TOOL = "tool"        # 工具调用
    SYSTEM = "system"    # 系统级请求
```

### 2.2 Intent 检测方法

**文件**: `backend/app/services/llm_service.py`

```python
async def detect_intent(self, user_message: str, context: Optional[dict] = None) -> dict:
    intent_schema = {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": ["chat", "image", "video", "audio", "tool", "system"]},
            "tone": {"type": "string"},
            "priority": {"type": "string", "enum": ["low", "normal", "high"]},
            "action": {"type": "string"},
            "memory_hint": {"type": "string"},
            "tool_hint": {"type": "string"},
            "confidence": {"type": "number"}
        },
        "required": ["intent", "confidence"]
    }
    
    system_prompt = """Analyze the user message and determine:
1. The primary intent:
   - chat: Normal conversation
   - image: User wants an image generated
   - video: User wants a video generated
   - audio: User wants to HEAR the response spoken aloud (e.g., "say goodnight to me", "I want to hear your voice", "tell me with your voice", "read this to me", "speak to me")
   - tool: User wants to use a specific tool
   - system: System-level request (settings, preferences)

2. The tone of the message
3. Priority level (low/normal/high)
4. Any action hints
5. Memory-related hints
6. Tool usage hints

Respond with valid JSON only."""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    response = await self.generate_structured(messages, intent_schema)
    return response.data
```

### 2.3 Audio Intent 触发示例

以下消息会触发 `audio` intent：

- "Say goodnight to me"
- "I want to hear your voice"
- "Tell me with your voice"
- "Read this to me"
- "Speak to me"
- "Can you say that out loud?"

---

## 三、TTS 生成

### 3.1 VoiceService

**文件**: `backend/app/services/voice_service.py`

```python
class VoiceService:
    async def generate_tts(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model_id: Optional[str] = None,
        speed: float = 1.0,
        provider: str = "elevenlabs",
        output_format: str = "mp3",
    ) -> dict:
        # 清理文本（移除 *action* 和 [emotion] 标记）
        cleaned_text = self._clean_text_for_tts(text)
        
        if provider == "elevenlabs":
            return await self._elevenlabs_tts(
                cleaned_text, voice_id, model_id, speed, output_format
            )
    
    async def _elevenlabs_tts(self, text: str, voice_id: str, ...) -> dict:
        response = await self.client.post(
            f"{self.settings.elevenlabs_base_url}/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": self.settings.elevenlabs_api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": model_id or "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "speed": speed,
                },
            },
        )
        
        return {
            "audio_url": audio_url,
            "duration": duration,
            "voice_id": voice_id,
            "provider": "elevenlabs",
        }
```

### 3.2 环境变量配置

**文件**: `backend/.env`

```
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_BASE_URL=https://api.elevenlabs.io/v1
```

### 3.3 支持的 TTS 提供商

| Provider | 描述 | 默认 Voice ID |
|----------|------|---------------|
| elevenlabs | ElevenLabs TTS API | 无（必须配置） |
| dashscope | 阿里云 DashScope | zhixiaoxia |

---

## 四、Credit 扣费

### 4.1 扣费逻辑

**文件**: `backend/app/services/database_service.py`

```python
VOICE_CREDIT_COST = 2  # 每条语音扣 2 credits

async def deduct_credits_by_firebase_uid(
    self, 
    firebase_uid: str, 
    amount: int
) -> tuple[bool, int, str]:
    """
    Deduct credits from user by firebase_uid.
    Returns (success, remaining_credits, error_message).
    """
    with self.transaction() as session:
        user = session.query(UserModel).filter(
            UserModel.firebase_uid == firebase_uid
        ).first()
        
        if not user:
            return False, 0, "User not found"
        
        if user.credits < amount:
            return False, user.credits, "Insufficient credits"
        
        user.credits -= amount
        user.total_credits_spent += amount
        session.flush()
        session.refresh(user)
        
        return True, user.credits, ""
```

### 4.2 Credit 不足处理

当 Credit 不足时，后端发送 SSE 错误事件：

```json
{
  "event": "error",
  "data": {
    "error_code": "insufficient_credits",
    "required": 2,
    "available": 0,
    "message": "Not enough credits for voice generation"
  }
}
```

前端收到事件后弹出 `InsufficientCreditsModal`，引导用户充值。

---

## 五、SSE 事件

### 5.1 语音相关事件类型

**文件**: `backend/app/core/events.py`

```python
class EventType(str, Enum):
    VOICE_NOTE_PENDING = "voice_note_pending"   # 语音生成中
    VOICE_NOTE_READY = "voice_note_ready"       # 语音生成成功
    VOICE_NOTE_FAILED = "voice_note_failed"     # 语音生成失败
    CREDIT_UPDATE = "credit_update"             # Credit 更新
```

### 5.2 事件数据结构

**VOICE_NOTE_PENDING**

```json
{
  "message_id": "msg_abc123"
}
```

**VOICE_NOTE_READY**

```json
{
  "message_id": "msg_abc123",
  "audio_url": "https://storage.example.com/audio/xxx.mp3",
  "duration": 5.2
}
```

**VOICE_NOTE_FAILED**

```json
{
  "message_id": "msg_abc123",
  "reason": "ElevenLabs API error: rate limit exceeded"
}
```

**CREDIT_UPDATE**

```json
{
  "credits": 98
}
```

---

## 六、前端组件

### 6.1 VoiceNotePlayer

**文件**: `frontend/src/components/chat/VoiceNotePlayer.tsx`

语音条播放组件，支持：

- 波形可视化（基于 message_id 生成伪随机波形）
- 播放/暂停控制
- 进度条拖动
- 时长显示
- 单例播放控制（同时只能播放一条语音）

**Props**:

```typescript
interface VoiceNotePlayerProps {
  messageId: string;      // 消息 ID
  audioUrl: string;       // 音频 URL
  duration: number;       // 时长（秒）
  isGenerating?: boolean; // 是否正在生成
  cost?: number;          // 消耗的 credits
  onPlayStart?: () => void;
  onPlayEnd?: () => void;
}
```

### 6.2 消息类型

**文件**: `frontend/src/types/chat.ts`

```typescript
export type MessageType = 'text' | 'image' | 'video' | 'voice_note';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  audio_url?: string;     // 语音 URL
  duration?: number;      // 语音时长
  // ... 其他字段
}
```

### 6.3 SSE 事件处理

**文件**: `frontend/src/contexts/ChatContext.tsx`

```tsx
case 'voice_note_pending':
  // 标记消息为语音生成中
  setMessages((prev) => prev.map((msg) =>
    msg.id === event.data.message_id
      ? { ...msg, metadata: { ...msg.metadata, voice_pending: true } }
      : msg
  ));
  break;

case 'voice_note_ready':
  // 更新消息的音频信息
  setMessages((prev) => prev.map((msg) =>
    msg.id === event.data.message_id
      ? {
          ...msg,
          audio_url: event.data.audio_url,
          duration: event.data.duration,
          message_type: 'voice_note',
          metadata: { ...msg.metadata, voice_pending: false },
        }
      : msg
  ));
  break;

case 'voice_note_failed':
  // 标记语音生成失败
  setMessages((prev) => prev.map((msg) =>
    msg.id === event.data.message_id
      ? { ...msg, metadata: { ...msg.metadata, voice_pending: false } }
      : msg
  ));
  break;

case 'error':
  if (event.data.error_code === 'insufficient_credits') {
    showInsufficientCreditsModal(event.data.required, event.data.available);
  }
  break;
```

---

## 七、完整聊天流程

**文件**: `backend/app/routers/chat.py`

```python
VOICE_CREDIT_COST = 2

@router.post("/stream")
async def chat_stream(request: Request, data: ChatStreamRequest) -> EventSourceResponse:
    llm = LLMService.get_instance()
    user_id = _get_user_id(request)  # firebase_uid
    
    async def event_generator():
        # 1. 获取角色信息
        character = await character_service.get_character_by_id(data.character_id)
        voice_id = character.get("voice_id") if character else None
        
        # 2. 初始化状态
        is_audio_intent = False
        credit_deducted = False
        remaining_credits = 0
        
        # 3. 检测 intent（如果有 voice_id）
        if voice_id:
            try:
                intent_result = await llm.detect_intent(data.message)
                is_audio_intent = intent_result.get("intent") == "audio"
            except Exception:
                is_audio_intent = False
        
        # 4. 检查并扣费
        if is_audio_intent:
            db_service = DatabaseService()
            success, remaining, error_msg = await db_service.deduct_credits_by_firebase_uid(
                user_id, VOICE_CREDIT_COST
            )
            if not success:
                yield SSEEvent(
                    event=EventType.ERROR,
                    data={
                        "error_code": "insufficient_credits",
                        "required": VOICE_CREDIT_COST,
                        "available": remaining,
                    }
                ).to_sse()
                is_audio_intent = False
            else:
                credit_deducted = True
                remaining_credits = remaining
        
        # 5. 生成文本回复（现有逻辑）
        # ... prompt building, streaming ...
        
        yield SSEEvent(
            event=EventType.TEXT_DONE,
            data={"content": full_response}
        ).to_sse()
        
        # 6. 生成语音（如果是 audio intent 且已扣费）
        if is_audio_intent and credit_deducted:
            message_id = f"msg_{uuid.uuid4().hex[:12]}"
            
            yield SSEEvent(
                event=EventType.VOICE_NOTE_PENDING,
                data={"message_id": message_id}
            ).to_sse()
            
            try:
                voice_service = VoiceService()
                audio_result = await voice_service.generate_tts(
                    text=full_response,
                    voice_id=voice_id,
                )
                
                yield SSEEvent(
                    event=EventType.VOICE_NOTE_READY,
                    data={
                        "message_id": message_id,
                        "audio_url": audio_result["audio_url"],
                        "duration": audio_result["duration"],
                    }
                ).to_sse()
                
                yield SSEEvent(
                    event=EventType.CREDIT_UPDATE,
                    data={"credits": remaining_credits}
                ).to_sse()
                
            except Exception as e:
                yield SSEEvent(
                    event=EventType.VOICE_NOTE_FAILED,
                    data={"message_id": message_id, "reason": str(e)}
                ).to_sse()
        
        # 7. 结束流
        yield SSEEvent(
            event=EventType.STREAM_END,
            data={"session_id": session_id}
        ).to_sse()
    
    return EventSourceResponse(event_generator())
```

---

## 八、边界情况处理

| 情况 | 处理方式 |
|------|----------|
| 角色无 voice_id | 跳过语音生成，只返回文本 |
| 用户 Credit 不足 | 发送 `insufficient_credits` 错误事件，前端弹窗引导充值 |
| TTS API 失败 | 发送 `voice_note_failed` 事件，文本正常显示 |
| Intent 检测失败 | 默认为 `chat` intent，不生成语音 |
| Guest 用户 | 与注册用户相同逻辑，检查 Credit |

---

## 九、相关文件清单

### 后端

| 文件 | 功能 |
|------|------|
| `backend/app/routers/chat.py` | 聊天流式接口，集成 audio intent + TTS |
| `backend/app/services/llm_service.py` | Intent 检测 |
| `backend/app/services/voice_service.py` | TTS 生成服务 |
| `backend/app/services/database_service.py` | Credit 扣费 |
| `backend/app/models/character.py` | Character 模型（含 voice_id） |
| `backend/app/models/voice.py` | Voice 相关模型 |
| `backend/app/core/events.py` | SSE 事件类型定义 |
| `backend/app/core/config.py` | ElevenLabs API 配置 |

### 前端

| 文件 | 功能 |
|------|------|
| `frontend/src/components/chat/VoiceNotePlayer.tsx` | 语音条播放组件 |
| `frontend/src/components/chat/MessageBubble.tsx` | 消息气泡（集成 VoiceNotePlayer） |
| `frontend/src/components/chat/InsufficientCreditsModal.tsx` | Credit 不足弹窗 |
| `frontend/src/contexts/ChatContext.tsx` | SSE 事件处理 |
| `frontend/src/pages/admin/CharacterEditPage.tsx` | 角色 Voice ID 配置 |
| `frontend/src/types/chat.ts` | 消息类型定义 |
| `frontend/src/types/character.ts` | VoiceProfile 类型定义 |
