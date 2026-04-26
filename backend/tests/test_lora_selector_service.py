from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.lora_selector_service import _build_system_prompt, select_lora


def test_build_system_prompt_uses_fallback_summary_when_description_empty():
    prompt = _build_system_prompt([
        {
            "name": "LoRA-A",
            "description": "",
            "example_prompt": "cinematic portrait, soft light",
        }
    ])
    assert '"LoRA-A"' in prompt
    assert "cinematic portrait, soft light" in prompt


@pytest.mark.asyncio
async def test_select_lora_accepts_fuzzy_name_from_llm():
    loras = [
        {
            "id": "1",
            "name": "35mm Photo - Flux/Z-Turbo",
            "model_name": "35mm Photo - Flux/Z-Turbo",
            "strength": 0.8,
            "trigger_word": "",
            "description": "",
            "example_prompt": "",
            "example_negative_prompt": "",
            "prompt_template_mode": "append_trigger",
        },
        {
            "id": "2",
            "name": "Aesthetic Amateur Photo",
            "model_name": "Aesthetic Amateur Photo",
            "strength": 0.8,
            "trigger_word": "",
            "description": "",
            "example_prompt": "",
            "example_negative_prompt": "",
            "prompt_template_mode": "append_trigger",
        },
    ]

    with patch("app.services.lora_selector_service._fetch_loras", new=AsyncMock(return_value=loras)):
        with patch("app.core.config.get_config_value", new=AsyncMock(return_value="test-key")):
            with patch("app.services.llm.providers.NovitaLLMProvider") as mock_provider_cls:
                mock_provider = MagicMock()
                mock_provider.generate_structured = AsyncMock(
                    return_value=MagicMock(data={"lora_name": "35mm photo flux z turbo"})
                )
                mock_provider_cls.return_value = mock_provider

                chosen = await select_lora(context="street portrait")

    assert chosen is not None
    assert chosen["id"] == "1"
