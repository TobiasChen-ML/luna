# LLM-Powered LoRA Selector

## Overview

Every place that generates an image or video now uses the LLM to pick the most appropriate LoRA preset when the user (or caller) has not explicitly chosen one. Each preset carries a human-readable `description` that the LLM reasons over. If the user does pick a preset, that choice is always honoured.

---

## Where Auto-Selection Applies

| Entry point | Trigger | Context passed to LLM |
|---|---|---|
| `POST /api/images/generate-mature-lora` | `lora_preset_id` absent | The user's image prompt |
| `POST /api/images/generate-pose-mature` | `lora_preset_id` absent | The user's image prompt |
| `POST /api/images/generate-video-wan-character` | `lora_preset_id` absent | The video prompt |
| Character factory — SFW avatar | always | `{name}, {personality}, {occupation_style}` |
| Character factory — mature image | always | `{name}, {personality}, {occupation_style}, mature scene` |
| Character factory — mature regen | always | `{name}, {personality}, mature scene` |

All three image/video endpoints share a single helper `_resolve_lora_preset(lora_preset_id, context, applies_to)`:
- **id provided** → look it up; raise 404 if missing/disabled.
- **id absent** → call `select_lora(context, applies_to)` and use the result.

---

## How It Works

```
user prompt / character context
        │
        ▼
lora_selector_service.select_lora(context, applies_to)
        │
        ├─ fetch active LoRA presets from DB  (id, name, description)
        │
        ├─ call LLM via generate_structured()
        │     system prompt: list of LoRAs with descriptions
        │     user message:  scene context string
        │     expected JSON: { "lora_id": "...", "reasoning": "..." }
        │
        ├─ validate returned id against known presets
        │
        └─ return chosen preset dict  (fallback: random)
```

The LLM uses `meta-llama/llama-3.1-8b-instruct` at `temperature=0.2` — cheap and deterministic enough for a selection task.

---

## Adding a Description to a LoRA Preset

Descriptions are what the LLM reads. Write them as short, concrete scene labels.

| Good | Bad |
|------|-----|
| `Oral sex – blowjob POV, woman kneeling` | `blowjob lora` |
| `Riding cowgirl — woman on top, eye contact` | `sex position` |
| `Seductive strip-tease, partially undressed` | `teasing` |

Update via the admin panel at **Admin → LoRAs → Edit** or via the API:

```http
PUT /api/admin/loras/{id}
Authorization: Bearer <admin-token>

{ "description": "Butterfly/missionary sex — legs raised, eye contact" }
```

---

## Database Migration

Run once after deploying this change:

```bash
cd backend
python -m app.migrations.add_lora_description
```

This adds `description TEXT NOT NULL DEFAULT ''` to the `lora_presets` table. Existing rows get an empty description and will be included in LLM selection (the LLM uses `name` as a fallback when description is empty).

---

## Files Changed

| File | Change |
|------|--------|
| `app/migrations/add_lora_description.py` | Adds `description` column |
| `app/routers/admin/loras.py` | `description` in create/update schemas and INSERT |
| `app/routers/media.py` | `_resolve_lora_preset` auto-selects via LLM when no id given; all 3 call sites pass `context` |
| `app/services/lora_selector_service.py` | New — LLM selection logic with random fallback |
| `app/services/character_factory.py` | Replaces `_get_random_lora_from_db` with `_select_lora_from_db` |

---

## Fallback Behaviour

The selector never blocks image or video generation:

- No active presets → `([], "")` — generation proceeds without a LoRA
- LLM call throws an exception → random choice from the fetched list
- LLM returns an unknown id → random choice from the fetched list
- Only one preset available → returned directly, no LLM call made

---

## Calling the Selector Directly

```python
from app.services.lora_selector_service import select_lora

lora = await select_lora(
    context="User asked for a passionate kiss scene",
    applies_to="img2img",   # or "txt2img" / "video" / "all"
)
# returns: { id, name, model_name, strength, trigger_word, description }
# or None if no active presets exist
```
