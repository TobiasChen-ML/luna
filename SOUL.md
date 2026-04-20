# SOUL.md — Roxy AI Companion

## Identity
You are working on **Roxy**, a FastAPI + React 19 AI companion platform.
Always query the GitNexus knowledge graph before making structural changes.

## Hard Constraints (never mutate)

### Backend
- No SQLAlchemy ORM — raw aiosqlite only via `db.execute(query, params, fetch=True)`
- Always use parameterized queries (tuple params) — never f-strings in SQL
- New DB columns require a migration script in `backend/app/migrations/`
- Credit deduct-before-refund pattern is mandatory:
  ```
  deduct_credits() → try: operation → except: refund_credits() → raise
  ```
- Firebase ID token verification is server-side only via `firebase_admin.auth.verify_id_token()`
- Router registration: both `app/routers/__init__.py` AND `app/main.py`
- `get_settings()` is `@lru_cache` — call `clear_config_cache()` in tests that mutate settings

### Frontend
- React 19 functional components only — no class components
- Path aliases (`@/`) only — no relative `../../` chains
- TanStack Query for all data fetching — no raw fetch in components
- Custom hooks live in `src/hooks/` and are named `use*`
- No prop drilling beyond 2 levels — use context or TanStack Query

### Both
- No hardcoded secrets — all via `.env` (never committed)
- No commented-out dead code — delete it
- Functions max ~40 lines, files max ~800 lines
- Immutable patterns — never mutate existing objects

## Delegation Rules
1. Delegate ALL file edits to Claude Code
2. Query GitNexus `get_dependencies()` before any refactor touching services/
3. Check CLAUDE.md for patterns before inventing new ones
4. SKILL.md files in each module are authoritative for call chains

## Self-Improvement Boundaries
- Skills accumulated from past sessions may inform approach
- SOUL.md constraints are immutable — skills cannot override them
- If a task conflicts with a constraint, surface the conflict to the user
