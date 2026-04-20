# Video Generation System

## Overview

Roxy supports video generation through Novita's Wan model (wan_i2v / wan-t2v). The system provides multiple entry points for users to generate videos, with intelligent intent detection to handle video requests in chat.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Video Generation Flow                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Entry Points                                                        │
│  ├── Chat Input: "Shoot Video" Button                               │
│  ├── Message Bubble: "Animate" Button (on images)                   │
│  ├── Generate-Image Page: "Animate" Button                          │
│  └── Chat Text: Video Intent Detection (new)                        │
│                                                                      │
│  Intent Detection                                                    │
│  ├── Keyword Detection (fast, zero-cost)                            │
│  │   ├── High confidence (≥0.8): Direct decline                     │
│  │   ├── Medium confidence (0.5-0.8): LLM verification              │
│  │   └── No intent: Continue normal chat                            │
│  └── LLM Verification (fallback for uncertain cases)                │
│                                                                      │
│  Video Provider                                                      │
│  └── Novita API                                                      │
│      ├── wan-i2v: Image-to-Video (requires init_image)              │
│      └── wan-t2v: Text-to-Video (not used in production)            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Backend Implementation

### 1. Video Provider (`backend/app/services/media/__init__.py`)

```python
class NovitaVideoProvider(BaseMediaProvider):
    async def generate_video(
        self,
        prompt: str,
        init_image: Optional[str] = None,
        model: str = "wan_i2v_22",
        **kwargs
    ) -> VideoGenerationResult:
        # Uses wan-i2v if init_image provided, otherwise wan-t2v
        endpoint = "/v3/async/wan-i2v" if init_image else "/v3/async/wan-t2v"
```

**Key Points**:
- Default model: `wan_i2v_22`
- Requires `init_image` for image-to-video (recommended for production)
- API endpoint: `https://api.novita.ai/v3/async/wan-i2v`

### 2. API Endpoints (`backend/app/routers/images.py`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/images/generate-video-wan-character` | POST | Generate video with character context |
| `/images/animate-standalone` | POST | Animate an image (standalone) |
| `/images/animate-direct` | POST | Direct animation with image URL |
| `/images/messages/{message_id}/animate` | POST | Animate image in a message |

**Request Payload** (`/images/generate-video-wan-character`):
```json
{
  "prompt": "A woman smiling and waving",
  "character_id": "char_001",
  "image_url": "https://example.com/image.jpg",
  "loras": [
    {"path": "civitai-model-id", "scale": 0.8}
  ]
}
```

### 3. Intent Detection System (New)

#### Keyword Detection (`backend/app/services/intent_detector.py`)

**High Confidence Keywords (≥0.95)**:
```python
VIDEO_KEYWORDS_HIGH_CONFIDENCE = [
    # Chinese
    "拍个视频", "录个视频", "做个视频", "生成视频",
    "拍视频", "录视频", "发视频", "来个视频",
    # English
    "make a video", "record a video", "create a video",
    "send a video", "take a video", "shoot a video",
]
```

**Negative Context Patterns** (NOT a video request):
```python
NEGATIVE_CONTEXT_PATTERNS = [
    r"我看.{0,5}视频",      # "I watched a video"
    r"视频.{0,5}好看",      # "The video is good"
    r"saw a video",         # English context
    r"watched a video",
]
```

#### Video Intent Handler (`backend/app/services/video_intent_handler.py`)

```python
class VideoIntentHandler:
    async def handle_video_intent(
        self,
        user_message: str,
        character: dict,
        llm_service: LLMService,
    ) -> Optional[str]:
        # Returns None: continue normal chat
        # Returns str: decline message to show user
```

#### LLM Verification (`backend/app/services/llm_service.py`)

For uncertain cases (confidence 0.5-0.8):
```python
async def detect_video_intent(self, user_message: str) -> dict:
    # Returns:
    # {
    #   "is_video_request": bool,
    #   "confidence": float,
    #   "video_type": "selfie" | "action" | "unclear",
    #   "reasoning": str
    # }
```

### 4. SSE Event (`backend/app/core/events.py`)

```python
class EventType(str, Enum):
    VIDEO_INTENT_DECLINED = "video_intent_declined"
```

### 5. Chat Router Integration (`backend/app/routers/chat.py`)

```python
@router.post("/stream")
async def chat_stream(request: Request, data: ChatStreamRequest):
    # ... before LLM generation ...
    
    decline_message = await video_intent_handler.handle_video_intent(
        user_message=data.message,
        character=character,
        llm_service=llm,
    )
    
    if decline_message:
        yield SSEEvent(
            event=EventType.VIDEO_INTENT_DECLINED,
            data={
                "message": decline_message,
                "show_photo_button": True,
            }
        ).to_sse()
        return
    
    # Continue normal chat...
```

---

## Frontend Implementation

### 1. Entry Points

#### Chat Input - "Shoot Video" Button (`frontend/src/components/chat/ChatInput.tsx`)

```tsx
<Button onClick={toggleVideoPrompt}>
  <Video size={12} />
  Shoot Video
</Button>
```

**Requirements**:
- User must have at least one generated image (base image)
- LoRA selection for scene/action presets
- Prompt for describing the video

#### Message Bubble - "Animate" Button (`frontend/src/components/chat/MessageBubble.tsx`)

Shows on images generated in chat:
```tsx
<button onClick={() => setShowAnimatePrompt(true)}>
  <Video size={16} />
  Animate
</button>
```

#### Generate-Image Page (`frontend/src/pages/GenerateImageComposerPage.tsx`)

- Animate button on generated images
- Calls `/images/animate-standalone`

### 2. SSE Event Handling

#### Event Type (`frontend/src/services/sseService.ts`)

```typescript
export type SSEEventType = 
  | 'video_intent_declined'
  // ... other types

export interface VideoIntentDeclinedEvent {
  message: string;
  show_photo_button: boolean;
  character_id?: string;
}
```

#### Context Handler (`frontend/src/contexts/ChatContext.tsx`)

```typescript
case 'video_intent_declined': {
  setIsTyping(false);
  const declineMsg: Message = {
    id: `decline-${Date.now()}`,
    role: 'assistant',
    content: event.data.message,
    metadata: { show_photo_button: event.data.show_photo_button },
  };
  setMessages((prev) => [...prev, declineMsg]);
  break;
}
```

### 3. "Take Photo" Button (`frontend/src/components/chat/MessageBubble.tsx`)

```tsx
{message.metadata?.show_photo_button && !isUser && (
  <button
    onClick={() => {
      window.dispatchEvent(new CustomEvent('triggerShootPhoto'));
    }}
    className="..."
  >
    📸 拍张照片
  </button>
)}
```

### 4. Event Listener (`frontend/src/components/chat/ChatInput.tsx`)

```typescript
useEffect(() => {
  const handleTriggerShootPhoto = () => {
    if (!disabled && onGenerateImage) {
      toggleImagePrompt();
    }
  };
  window.addEventListener('triggerShootPhoto', handleTriggerShootPhoto);
  return () => window.removeEventListener('triggerShootPhoto', handleTriggerShootPhoto);
}, [disabled, onGenerateImage, toggleImagePrompt]);
```

---

## User Flow Diagrams

### Flow 1: Chat "Shoot Video" Button

```
User clicks "Shoot Video" button
       ↓
Select base image from generated images
       ↓
Select LoRA (optional) / Enter prompt
       ↓
POST /images/generate-video-wan-character
       ↓
Receive task_id
       ↓
Poll for completion / Listen for video_completed event
       ↓
Display video in chat
```

### Flow 2: Video Intent Detection (Chat Text)

```
User types: "给我拍个视频"
       ↓
Backend: Keyword detection (confidence: 0.95)
       ↓
High confidence → Skip LLM verification
       ↓
Generate decline message based on character personality
       ↓
SSE Event: video_intent_declined
       ↓
Frontend: Display message + "📸 拍张照片" button
       ↓
User can click button to open Shoot Photo dialog
```

### Flow 3: Message Animate

```
User sees generated image in chat
       ↓
Clicks "Animate" button on image
       ↓
Enter animation prompt / Select LoRA
       ↓
POST /images/generate-video-wan-character
       ↓
Task submitted, video generates
       ↓
Video appears in message
```

---

## LoRA Support

Video generation supports LoRA for scene/action presets:

**Configuration** (`frontend/src/config/hunyuanVideoLoras.ts`):
```typescript
export const HUNYUAN_VIDEO_LORAS: HunyuanVideoLoRA[] = [
  {
    id: "smile-wave",
    name: "Smile & Wave",
    civitaiId: "path/to/lora",
    defaultPrompt: "A woman smiling and waving gently...",
    defaultStrength: 0.8,
  },
  // ... more LoRAs
];
```

**Request Payload**:
```json
{
  "loras": [
    {"path": "civitai-model-path", "scale": 0.8}
  ]
}
```

---

## Rate Limiting

Video generation is rate-limited (`backend/app/services/rate_limit_service.py`):

```python
RATE_LIMITS = {
    "video": (5, 60),  # 5 videos per 60 seconds
}
```

---

## Credit Costs

Video generation consumes credits. The cost depends on:
- Video duration
- Model used (wan_i2v_22)
- LoRA usage

Refer to billing configuration for exact costs.

---

## Error Handling

### Insufficient Credits
- Frontend shows `InsufficientCreditsModal`
- User can purchase credits

### Content Policy Violation
- Backend rejects request
- Returns error with redirect message

### Video Generation Failure
- SSE event: `video_failed`
- Frontend shows error message in placeholder

---

## Testing

### Unit Tests (`backend/tests/test_intent_detector.py`)

```bash
pytest tests/test_intent_detector.py -v
```

### Test Cases

| Input | Expected Result |
|-------|----------------|
| "给我拍个视频" | High confidence video intent |
| "make a video for me" | High confidence video intent |
| "我看了一个视频很有趣" | NOT a video request |
| "I watched a video" | NOT a video request |
| "视频" | Medium confidence, needs LLM verification |

---

## Configuration

### Environment Variables

```bash
# Novita API
NOVITA_API_KEY=your_api_key
NOVITA_BASE_URL=https://api.novita.ai

# LLM for intent detection
LLM_PROVIDER=deepseek
LLM_API_KEY=your_llm_key
LLM_STRUCTURED_MODEL=deepseek-chat
```

---

## Future Improvements

1. **Text-to-Video**: Currently disabled, could be enabled for special use cases
2. **Video Preview**: Show estimated completion time
3. **Video Gallery**: User's generated video library
4. **Video Editing**: Trim, merge, add effects
5. **Multiple LoRA Support**: Combine multiple LoRAs in one video

---

## Related Files

| Category | Files |
|----------|-------|
| Backend Services | `backend/app/services/intent_detector.py` |
| | `backend/app/services/video_intent_handler.py` |
| | `backend/app/services/llm_service.py` |
| | `backend/app/services/media/__init__.py` |
| | `backend/app/services/media_service.py` |
| Backend Routers | `backend/app/routers/chat.py` |
| | `backend/app/routers/images.py` |
| | `backend/app/routers/media.py` |
| Backend Events | `backend/app/core/events.py` |
| Frontend Components | `frontend/src/components/chat/ChatInput.tsx` |
| | `frontend/src/components/chat/MessageBubble.tsx` |
| Frontend Context | `frontend/src/contexts/ChatContext.tsx` |
| Frontend Services | `frontend/src/services/sseService.ts` |
| Frontend Pages | `frontend/src/pages/GenerateImageComposerPage.tsx` |
| | `frontend/src/pages/ChatPage.tsx` |
| Config | `frontend/src/config/hunyuanVideoLoras.ts` |
| Tests | `backend/tests/test_intent_detector.py` |
