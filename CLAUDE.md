# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Roxy** is an AI companion chat platform where users interact with AI characters via real-time streaming chat, voice, image/video generation, and a scripted story system. The monorepo has a React 19 frontend (PWA) and a FastAPI backend with SQLite (dev) / PostgreSQL (prod).

---

## Quick Start Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8999
pytest                                              # All tests
pytest tests/test_auth.py::test_login -v           # Single test
pytest --cov=app --cov-report=term-missing         # Coverage
```

### Frontend
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build
npm run lint
npm test           # Vitest unit tests (no watch)
npm run test:e2e   # Playwright E2E tests
npm run test:e2e:ui   # Playwright with UI mode
```

### Both Together
```bash
bash dev.sh        # Linux/macOS — starts backend :8999 + frontend :5173
dev.bat            # Windows
docker-compose up --build
```

### Database Migration
```bash
cd backend
python -m app.migrations.add_credit_tables
python -m app.migrations.migrate_memory_embeddings --rebuild   # Vector DB migration
```

---

## Architecture

### Backend (`backend/app/`)

**Entry point:** `main.py` — registers all routers, CORS, rate-limiting middleware, lifespan (DB connect + prompt template init).

**Config hierarchy** (`core/config.py`): Settings from `.env` via pydantic-settings. A `get_config_value()` async helper checks Redis first (runtime-editable), then env vars, then Settings — allowing live config overrides without restarts.

**Database** (`core/database.py`): Raw aiosqlite singleton — no SQLAlchemy ORM. All tables are created via `CREATE TABLE IF NOT EXISTS` in `_create_tables()`. Migrations are standalone scripts in `app/migrations/`.

**Auth** (`core/dependencies.py`): Supports two auth backends simultaneously — Firebase ID tokens and internal JWT. The `get_current_user_required` dependency checks `Authorization: Bearer <token>` and tries Firebase first, falls back to JWT.

**Layer structure:**
```
Router → Service(s) → crud/ or DatabaseService → db.execute()
```
- `crud/` — thin data-access functions (one file per entity)
- `services/` — business logic; `services/llm/` and `services/media/` are subdirectories
- `models/` — Pydantic models per feature (character, billing, memory, etc.)
- `schemas/` — request/response schemas used by routers

**Key services:** `llm_service.py` (orchestrates LLM calls), `prompt_builder.py` (constructs system prompts), `character_service.py`, `relationship_service.py`, `credit_service.py`, `script_service.py`, `chat_history_service.py`, `memory_service.py` (vector-enhanced memory), `embedding_service.py` (text embeddings), `voice_service.py` / `voice_call_service.py` (ElevenLabs + LiveKit), `story_service.py`, `audit_service.py`, `group_chat_service.py`.

**LLM abstraction** (`services/llm/providers.py`): `NovitaLLMProvider` (default), plus DeepSeek, OpenAI, Ollama. Provider is selected by `LLM_PROVIDER` env var and implements `generate()` / `generate_stream()`. Primary model: `meta-llama/llama-3.3-70b-instruct`; structured outputs use `deepseek/deepseek-v3.2`.

**Chat pipeline** (`routers/chat.py`): SSE streaming via `sse-starlette`. The `/api/chat/stream` endpoint runs: credit check → intent detection → prompt building → LLM stream → relationship update → optional TTS/image generation.

**Intent routing** (`services/intent_router.py`, `services/inference_router.py`): Classifies messages and routes simple requests (greetings, short questions) to local Ollama for <200ms latency; complex/emotional requests go to cloud LLM.

**Script system** (`routers/scripts.py`, `services/script_service.py`): Branching narrative trees (nodes stored as JSON in `scripts` / `script_nodes` tables). Chat sessions track `script_id` and `script_node_id`.

**Memory system** (`services/memory_service.py`, `services/vector_store.py`): ChromaDB-backed semantic search with time decay and importance weighting. Embeddings via `all-MiniLM-L6-v2` (384-dim) with OpenAI/Cloudflare fallback.

**Rate limiting:** `middleware/security_middleware.py` — `RateLimitMiddleware` applied globally in `main.py`.

**Character media generation** (`services/character_factory.py`): Three-step pipeline run by `_generate_character_images()`:
1. **SFW avatar** — Novita txt2img full-body selfie (768×1024) with a randomly selected background (beach, hotel, gym, etc. weighted by occupation). `cover_url` is set to the same URL — no separate cover image.
2. **Mature image** — Novita img2img with IPAdapter referencing the SFW avatar (character consistency) plus any active LoRAs fetched from the `lora_presets` DB table (`applies_to = 'img2img'`). `mature_cover_url` is set to the same URL — no separate mature cover.
3. **Mature video** — Novita WAN2.1 img2video (`/v3/async/wan-i2v`), launched as an `asyncio.create_task` after the character is saved, polls for completion, then updates `mature_video_url` in DB.

**LoRA management** (`routers/admin/loras.py`, `config/lora_configs.py`): Admin can CRUD LoRA presets in `lora_presets` table. `applies_to` field scopes LoRAs to `txt2img`, `img2img`, `video`, or `all`.

**Router groups:**
- `/api/auth` — Firebase + JWT login, registration, Telegram Mini App auth
- `/api/chat` — SSE streaming chat, history
- `/api/character` — Character CRUD, public catalog, UGC review
- `/api/media` — Async image/video generation tasks (polled via `/api/tasks`)
- `/api/billing` — Stripe + CCBill + USDT + Telegram Stars payments
- `/api/world` — World-building (character/story/context/relationship sub-routers)
- `/api/scripts` — Branching narrative scripts; `/api/script-library` for public library
- `/api/voice` / `/api/voices` — Voice management, ElevenLabs, LiveKit calls
- `/api/story` — Story generation and management
- `/api/admin/*` — Admin console (protected by `ADMIN_PASSWORD`); sub-routers for prompts, scripts, credits, audit
- `/api/gateway` — External API key access (legacy + v2)
- `/api/inference` — Intent routing, inference health, local model status
- `/api/context` — Memory management, vector store operations
- `/api/pipeline` — Batch processing pipelines
- `/api/ops` — Operational utilities

### Frontend (`frontend/src/`)

**Routing:** `App.tsx` — all routes inline with `<Routes>`. Language prefix (`/:lang?`) wraps all routes; `LanguageHandler` syncs i18next to the URL param.

**Auth flow:** `AuthContext.tsx` wraps Firebase auth + fetches backend profile. Token storage is abstracted in `lib/tokenStorage.ts` (HttpOnly cookie capable). `ProtectedRoute` guards authenticated pages; `GuestContext` handles unauthenticated sessions.

**API calls:** `services/api.ts` is the central Axios client with 401 auto-refresh interceptor. Feature-specific services (`billingService.ts`, `storyService.ts`, `characterService.ts`, etc.) call it. TanStack Query (`useQuery`/`useMutation`) used in components.

**Real-time:** `sseService.ts` handles SSE from `/api/chat/stream`. `ChatContext.tsx` manages active session. `realtimeVoiceService.ts` / `voiceStreamClient.ts` handle LiveKit WebRTC voice.

**Contexts:**
- `AuthContext` — Firebase user + backend profile
- `ChatContext` — Active chat session
- `GuestContext` — Unauthenticated session
- `GeoContext` — Region/age-gate logic
- `AgeGateContext` — 18+ gate state
- `TelegramContext` — Telegram WebApp detection
- `AudioFocusContext` — Audio playback coordination
- `CharacterWizardContext` — Multi-step character creation state

**Custom hooks:** `src/hooks/` — `useAdminAuth.ts`, `useRecaptcha.ts`, Telegram button hooks.

**E2E tests:** `frontend/e2e/` — Playwright specs organized under `admin/` and `chat/`. A test-only login endpoint `POST /api/auth/test-login` exists for E2E setup.

**PWA:** `vite.config.ts` via `vite-plugin-pwa`. NetworkFirst for `/api/`, CacheFirst for static assets. Max cache file size: 10 MB.

---

## Key Patterns

### Adding a Backend Endpoint
1. Pydantic schema in `app/schemas/<feature>.py` or `app/models/<feature>.py`
2. Data access in `app/crud/<feature>.py`
3. Business logic in `app/services/<feature>_service.py`
4. Route in `app/routers/<feature>.py`; register in `app/routers/__init__.py` + `main.py`
5. Test in `tests/test_<feature>.py`

### Database Access
Use `db.execute(query, params, fetch=True/fetch_all=True)` — no ORM. Always parameterized queries (tuple params), never f-strings.

```python
from app.core.database import db

row = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,), fetch=True)
rows = await db.execute("SELECT * FROM characters WHERE is_public = 1", fetch_all=True)
```

### Credit Deduction Pattern
Always deduct before expensive operations; refund on failure.

```python
await credit_service.deduct_credits(user_id, cost, "image_generation")
try:
    result = await generate_image(...)
except Exception:
    await credit_service.refund_credits(user_id, cost, "image_generation_failed")
    raise
```

### SSE Streaming Response
```python
from sse_starlette.sse import EventSourceResponse

async def stream_generator():
    async for token in llm_service.stream(...):
        yield {"data": token}

return EventSourceResponse(stream_generator())
```

---

## Configuration

**Backend `.env`** (in `backend/`):
```
ENVIRONMENT=development
DATABASE_URL=sqlite:///./roxy.db
REDIS_URL=redis://localhost:6379/0
LLM_PROVIDER=novita
LLM_API_KEY=...
NOVITA_API_KEY=...
FAL_API_KEY=...
ELEVENLABS_API_KEY=...
STRIPE_SECRET_KEY=...
FIREBASE_PROJECT_ID=...
FIREBASE_CREDENTIALS_PATH=../config/firebase-credentials.json
JWT_SECRET_KEY=...
ADMIN_PASSWORD=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
LIVEKIT_WS_URL=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_ENDPOINT_URL=...

# Vector DB / Embedding (optional)
EMBEDDING_PROVIDER=local          # local | openai | cloudflare
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./chroma_db
VECTOR_SEARCH_ENABLED=true

# Edge Inference (optional)
LOCAL_INFERENCE_ENABLED=false
LOCAL_MODEL_URL=http://localhost:11434
LOCAL_MODEL_NAME=qwen2.5:1.5b
INTENT_ROUTING_ENABLED=true
INTENT_CONFIDENCE_THRESHOLD=0.8
```

**Runtime config override:** Keys like LLM model and feature flags can be updated via the admin panel, stored in Redis, overriding `.env` without restart.

---

## Testing

- **Backend config:** `pytest.ini` — `asyncio_mode = auto`, tests in `tests/`, `-v --tb=short`
- **Fixtures:** `tests/conftest.py` — async test client, mock DB, mock Firebase
- **Pattern:** Mock external APIs (Firebase, Redis, ElevenLabs, Stripe) in unit tests; in-memory SQLite for integration tests
- **Frontend:** Vitest unit tests co-located or in `src/__tests__/`; Playwright E2E in `frontend/e2e/`

---

## Gotchas

- **No SQLAlchemy ORM** — schema managed via raw SQL in `database.py:_create_tables()`. New columns need a migration script in `app/migrations/`.
- **`get_settings()` is cached** (`@lru_cache`) — call `clear_config_cache()` in tests that mutate settings.
- **`ENVIRONMENT=production`** enforces: JWT_SECRET ≥ 32 chars, no wildcard CORS, ADMIN_PASSWORD ≥ 12 chars.
- **Router registration** must happen in both `app/routers/__init__.py` (export) and `app/main.py` (mount).
- Frontend dev server proxies `/api/*` → `http://localhost:8999` (configured in `vite.config.ts`).
- `services/media/` and `services/llm/` are subdirectories with their own `__init__.py`.

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **Roxy** (13462 symbols, 31369 relationships, 300 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/Roxy/context` | Codebase overview, check index freshness |
| `gitnexus://repo/Roxy/clusters` | All functional areas |
| `gitnexus://repo/Roxy/processes` | All execution flows |
| `gitnexus://repo/Roxy/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
