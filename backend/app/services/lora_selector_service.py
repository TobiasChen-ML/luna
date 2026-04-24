"""
LLM-powered LoRA selector.

Fetches active LoRA presets from the DB, then uses `generate_structured` to
have the LLM pick the most contextually appropriate one based on a free-text
scene description.  Falls back to random selection if the LLM call fails or
returns an invalid choice.
"""

import json
import logging
import random
from typing import Optional

from app.core.database import db

logger = logging.getLogger(__name__)

_SELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "lora_name": {
            "type": "string",
            "description": "The exact name of the selected LoRA preset, copied verbatim from the list",
        },
        "reasoning": {
            "type": "string",
            "description": "One sentence explaining why this LoRA fits the context",
        },
    },
    "required": ["lora_name"],
}


async def _fetch_loras(applies_to: str) -> list[dict]:
    try:
        rows = await db.execute(
            "SELECT id, name, model_name, strength, trigger_word, description, "
            "example_prompt, example_negative_prompt, prompt_template_mode "
            "FROM lora_presets "
            "WHERE is_active = 1 AND (applies_to = ? OR applies_to = 'all') AND provider = 'novita'",
            (applies_to,),
            fetch_all=True,
        )
        return [dict(r) for r in (rows or [])]
    except Exception as e:
        logger.warning(f"[LoraSelector] DB fetch failed: {e}")
        return []


def _build_system_prompt(loras: list[dict]) -> str:
    options = "\n".join(
        f"  - \"{l['name']}\": {l['description'] or '(no description)'}"
        for l in loras
    )
    return (
        "You are an image-generation assistant. Given a scene context, pick the "
        "single LoRA preset that best matches it from the list below.\n\n"
        f"Available LoRAs:\n{options}\n\n"
        'Return JSON with key "lora_name" set to the EXACT name string from the list above. '
        "Do not invent names."
    )


async def select_lora(context: str, applies_to: str = "img2img") -> Optional[dict]:
    """
    Use the LLM to pick the best LoRA for *context*.

    Returns one dict from lora_presets (with id, name, model_name, strength,
    trigger_word, description, example_prompt, example_negative_prompt,
    prompt_template_mode), or None if no LoRAs are available.
    Falls back to random if the LLM fails or picks an invalid id.
    """
    loras = await _fetch_loras(applies_to)
    if not loras:
        return None

    if len(loras) == 1:
        return loras[0]

    lora_map = {l["name"]: l for l in loras}

    try:
        from app.services.llm.providers import NovitaLLMProvider
        from app.services.llm import LLMRequest, Message
        from app.core.config import get_config_value

        api_key = await get_config_value("LLM_API_KEY")
        if not api_key:
            logger.warning("[LoraSelector] LLM_API_KEY not configured, falling back to random")
            return random.choice(loras)

        provider = NovitaLLMProvider(api_key=api_key)
        request = LLMRequest(
            messages=[
                Message(role="system", content=_build_system_prompt(loras)),
                Message(role="user", content=f"Scene context: {context}"),
            ],
            model="meta-llama/llama-3.1-8b-instruct",
            temperature=0.2,
            max_tokens=200,
        )

        structured = await provider.generate_structured(request, _SELECTION_SCHEMA)
        raw_lora_name = structured.data.get("lora_name")
        if isinstance(raw_lora_name, str):
            chosen_name = raw_lora_name.strip()
        elif raw_lora_name is False or raw_lora_name is None:
            chosen_name = ""
        else:
            chosen_name = str(raw_lora_name).strip()
        reasoning = structured.data.get("reasoning", "")

        # Some LLM calls return boolean false/string "false" for invalid picks.
        if chosen_name.lower() in {"false", "null", "none", "0"}:
            chosen_name = ""

        if not chosen_name:
            logger.warning("[LoraSelector] LLM returned empty lora_name, falling back to random.")
        elif chosen_name in lora_map:
            logger.info(
                f"[LoraSelector] LLM chose '{chosen_name}' for applies_to={applies_to}. "
                f"Reason: {reasoning}"
            )
            return lora_map[chosen_name]
        else:
            logger.warning(
                f"[LoraSelector] LLM returned unknown name '{chosen_name}', falling back to random."
            )
    except Exception as e:
        logger.warning(f"[LoraSelector] LLM selection failed: {e}, falling back to random.")

    chosen = random.choice(loras)
    logger.info(f"[LoraSelector] Random fallback selected '{chosen['name']}'.")
    return chosen
