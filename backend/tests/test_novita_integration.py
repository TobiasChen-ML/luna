"""
Integration smoke tests for Novita API.

Requires NOVITA_API_KEY in the environment. Skipped automatically in CI
when the key is absent. Run manually with:

    NOVITA_API_KEY=sk_... pytest tests/test_novita_integration.py -v -m integration
"""

import os
import pytest

from app.services.media import (
    NovitaImageProvider,
    NovitaVideoProvider,
    ZImageTurboLoraProvider,
)

_API_KEY = os.environ.get("NOVITA_API_KEY", "")
_BASE_URL = os.environ.get("NOVITA_BASE_URL", "https://api.novita.ai/v3")

pytestmark = pytest.mark.integration

skip_no_key = pytest.mark.skipif(
    not _API_KEY,
    reason="NOVITA_API_KEY not set — skipping live integration tests",
)


def _image_provider() -> NovitaImageProvider:
    return NovitaImageProvider(api_key=_API_KEY, base_url=_BASE_URL)


def _video_provider() -> NovitaVideoProvider:
    return NovitaVideoProvider(api_key=_API_KEY, base_url=_BASE_URL)


# ---------------------------------------------------------------------------
# URL sanity checks (no network needed)
# ---------------------------------------------------------------------------


def test_image_provider_endpoints_no_double_v3():
    """txt2img / img2img / task-result URLs must be well-formed (no double /v3)."""
    provider = _image_provider()
    base = provider.base_url  # "https://api.novita.ai/v3"

    assert f"{base}/async/txt2img" == "https://api.novita.ai/v3/async/txt2img"
    assert f"{base}/async/img2img" == "https://api.novita.ai/v3/async/img2img"
    assert f"{base}/async/task-result" == "https://api.novita.ai/v3/async/task-result"
    assert "/v3/v3/" not in base


def test_video_provider_endpoints_no_double_v3():
    """wan-i2v and wan-t2v endpoints must not produce a double /v3 path."""
    provider = _video_provider()
    i2v_url = f"{provider.base_url}/async/wan-i2v"
    t2v_url = f"{provider.base_url}/async/wan-t2v"
    task_url = f"{provider.base_url}/async/task-result"

    assert i2v_url == "https://api.novita.ai/v3/async/wan-i2v"
    assert t2v_url == "https://api.novita.ai/v3/async/wan-t2v"
    assert task_url == "https://api.novita.ai/v3/async/task-result"


def test_z_image_turbo_endpoint_no_double_v3():
    """ZImageTurboLora endpoint must not produce a double /v3 path."""
    provider = ZImageTurboLoraProvider(api_key="dummy", base_url=_BASE_URL)
    full_url = f"{provider.base_url}{provider.ENDPOINT}"
    assert full_url == "https://api.novita.ai/v3/async/z-image-turbo-lora", (
        f"Double /v3 detected: {full_url}"
    )


# ---------------------------------------------------------------------------
# Live API tests (require NOVITA_API_KEY)
# ---------------------------------------------------------------------------


@skip_no_key
@pytest.mark.asyncio
async def test_txt2img_submit_and_poll():
    """Submit a txt2img task and poll until success."""
    provider = _image_provider()

    task_id = await provider.txt2img_async(
        prompt="a beautiful anime girl with long black hair, smiling, portrait, high quality",
        negative_prompt="low quality, blur, ugly",
        width=768,
        height=1024,
        steps=20,
    )
    assert task_id, "Expected a non-empty task_id from txt2img_async"

    result = await provider.wait_for_task(task_id, timeout_seconds=120, poll_interval=3.0)

    assert result.status == "TASK_STATUS_SUCCEED", (
        f"txt2img failed: {result.error}"
    )
    assert result.image_url, "Expected image_url in successful result"


@skip_no_key
@pytest.mark.asyncio
async def test_wan_t2v_submit():
    """Submit a wan-t2v task and confirm API accepts it (task_id returned)."""
    provider = _video_provider()

    task_id = await provider.generate_video_async(
        prompt="a girl smiling gently",
        width=832,
        height=480,
        steps=10,
        guidance_scale=5.0,
        flow_shift=5.0,
        seed=42,
        enable_safety_checker=False,
    )
    assert task_id, "Expected a non-empty task_id from generate_video_async (wan-t2v)"
