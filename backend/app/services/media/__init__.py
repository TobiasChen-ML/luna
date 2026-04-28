import logging
import base64
import asyncio
from typing import Optional, Any
from dataclasses import dataclass, field
from app.core.config import get_settings

logger = logging.getLogger(__name__)

NOVITA_CALLBACK_PATH = "/api/images/callbacks/novita"


async def _get_novita_webhook_url() -> Optional[str]:
    try:
        from app.core.config import get_config_value

        settings = get_settings()
        base_url = await get_config_value(
            "NOVITA_WEBHOOK_BASE_URL",
            getattr(settings, "novita_webhook_base_url", None),
        )
    except Exception as e:
        logger.warning("Failed to resolve Novita webhook URL: %s", e)
        return None

    if not base_url:
        return None

    normalized = str(base_url).strip().rstrip("/")
    if not normalized:
        return None
    return f"{normalized}{NOVITA_CALLBACK_PATH}"


async def _apply_novita_webhook(extra: dict[str, Any]) -> dict[str, Any]:
    webhook_url = await _get_novita_webhook_url()
    if webhook_url:
        extra["webhook"] = {"url": webhook_url}
    return extra


@dataclass
class ImageGenerationResult:
    image_url: str
    seed: Optional[int] = None
    width: int = 512
    height: int = 512
    task_id: Optional[str] = None


@dataclass
class VideoGenerationResult:
    video_url: str
    duration: Optional[float] = None
    thumbnail_url: Optional[str] = None
    task_id: Optional[str] = None


@dataclass
class AudioGenerationResult:
    audio_url: str
    duration: Optional[float] = None
    voice_id: Optional[str] = None


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
    strength: float = 0.45
    model_name: str = "ip-adapter_sdxl.bin"


@dataclass
class ControlNetConfig:
    model_name: str
    image_base64: str
    strength: float = 0.65
    preprocessor: Optional[str] = None
    guidance_start: float = 0.0
    guidance_end: float = 0.8


class BaseMediaProvider:
    def __init__(self, api_key: str, base_url: str, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
    
    async def health_check(self) -> bool:
        return True
    
    async def _download_image_base64(self, image_url: str) -> str:
        import httpx
        import io
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            content = response.content
            content_type = (response.headers.get("content-type") or "").lower()

            # Novita img2img rejects WEBP input (INVALID_IMAGE_FORMAT).
            # Normalize unsupported source formats to JPEG before base64 encoding.
            if "image/webp" in content_type or image_url.lower().split("?", 1)[0].endswith(".webp"):
                try:
                    from PIL import Image

                    with Image.open(io.BytesIO(content)) as img:
                        buf = io.BytesIO()
                        img.convert("RGB").save(buf, format="JPEG", quality=95)
                        content = buf.getvalue()
                    logger.info("Converted WEBP source to JPEG for img2img/IPAdapter request.")
                except Exception as e:
                    logger.warning("WEBP->JPEG conversion failed, using raw bytes: %s", e)

            return base64.b64encode(content).decode("utf-8")


class NovitaImageProvider(BaseMediaProvider):
    DEFAULT_MODEL = "juggernautXL_v9Rdphoto2Lightning_285361.safetensors"
    DEFAULT_MODEL_SD15 = "realisticVisionV51_v51VAE_94301.safetensors"
    DEFAULT_NEGATIVE_PROMPT = "explicit, adult content, low quality, bad anatomy, blur, blurry, ugly, wrong proportions, watermark, bad eyes, bad hands, bad arms, deformed, disfigured"
    
    async def _get_txt2img_model(self, model: Optional[str] = None) -> str:
        if model:
            return model
        try:
            from app.core.config import get_config_value
            val = await get_config_value("IMAGE_TXT2IMG_MODEL")
            if val:
                return val
        except Exception:
            pass
        return self.DEFAULT_MODEL
    
    async def _get_img2img_model(self, model: Optional[str] = None) -> str:
        if model:
            return model
        try:
            from app.core.config import get_config_value
            val = await get_config_value("IMAGE_IMG2IMG_MODEL")
            if val:
                return val
        except Exception:
            pass
        return self.DEFAULT_MODEL
    
    async def _get_img2img_strength(self, strength: Optional[float] = None) -> float:
        if strength is not None:
            return strength
        try:
            from app.core.config import get_config_value
            val = await get_config_value("IMG2IMG_STRENGTH")
            if val:
                return float(val)
        except Exception:
            pass
        return 0.45

    async def _get_ip_adapter_strength(self, strength: Optional[float] = None) -> float:
        if strength is not None:
            return strength
        try:
            from app.core.config import get_config_value
            val = await get_config_value("IP_ADAPTER_STRENGTH")
            if val:
                return float(val)
        except Exception:
            pass
        return 0.45

    async def _get_openpose_strength(self, strength: Optional[float] = None) -> float:
        if strength is not None:
            return strength
        try:
            from app.core.config import get_config_value
            val = await get_config_value("OPENPOSE_CONTROLNET_STRENGTH")
            if val:
                return float(val)
        except Exception:
            pass
        return 0.65
    
    async def _get_img2img_sampler(self, sampler_name: Optional[str] = None) -> str:
        if sampler_name:
            return sampler_name
        try:
            from app.core.config import get_config_value
            val = await get_config_value("IMG2IMG_SAMPLER")
            if val:
                return val
        except Exception:
            pass
        return "DPM++ 2M"
    
    async def _get_image_width(self, width: int = 1024) -> int:
        if width != 1024:
            return width
        try:
            from app.core.config import get_config_value
            val = await get_config_value("IMAGE_DEFAULT_WIDTH")
            if val:
                return int(val)
        except Exception:
            pass
        return width
    
    async def _get_image_height(self, height: int = 1024) -> int:
        if height != 1024:
            return height
        try:
            from app.core.config import get_config_value
            val = await get_config_value("IMAGE_DEFAULT_HEIGHT")
            if val:
                return int(val)
        except Exception:
            pass
        return height
    
    async def _get_image_steps(self, steps: int = 20) -> int:
        if steps != 20:
            return steps
        try:
            from app.core.config import get_config_value
            val = await get_config_value("IMAGE_DEFAULT_STEPS")
            if val:
                return int(val)
        except Exception:
            pass
        return steps
    
    async def _get_image_cfg(self, guidance_scale: float = 7.5) -> float:
        if guidance_scale != 7.5:
            return guidance_scale
        try:
            from app.core.config import get_config_value
            val = await get_config_value("IMAGE_DEFAULT_CFG")
            if val:
                return float(val)
        except Exception:
            pass
        return guidance_scale

    def _filter_sdxl_loras(self, loras: Optional[list["LoRAConfig"]]) -> Optional[list["LoRAConfig"]]:
        """Drop LoRAs whose model_name uses civitai: format — incompatible with SDXL endpoints."""
        if not loras:
            return loras
        compatible = [l for l in loras if not l.model_name.startswith("civitai:")]
        if len(compatible) < len(loras):
            skipped = [l.model_name for l in loras if l.model_name.startswith("civitai:")]
            logger.warning(
                "Skipping %d civitai-format LoRA(s) incompatible with SDXL txt2img: %s",
                len(skipped), skipped,
            )
        return compatible or None

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
        image_num: int = 1,
        sampler_name: str = "DPM++ 2M",
        loras: Optional[list[LoRAConfig]] = None,
        restore_faces: bool = False,
    ) -> str:
        import httpx
        
        resolved_model = await self._get_txt2img_model(model)
        resolved_width = await self._get_image_width(width)
        resolved_height = await self._get_image_height(height)
        resolved_steps = await self._get_image_steps(steps)
        resolved_cfg = await self._get_image_cfg(guidance_scale)
        
        payload = {
            "extra": await _apply_novita_webhook({"response_image_type": "jpeg"}),
            "request": {
                "model_name": resolved_model,
                "prompt": prompt,
                "negative_prompt": negative_prompt or self.DEFAULT_NEGATIVE_PROMPT,
                "width": resolved_width,
                "height": resolved_height,
                "image_num": image_num,
                "steps": resolved_steps,
                "seed": seed,
                "guidance_scale": resolved_cfg,
                "sampler_name": sampler_name,
                "clip_skip": 1,
                "restore_faces": restore_faces,
            }
        }
        
        compatible_loras = self._filter_sdxl_loras(loras)
        if compatible_loras:
            payload["request"]["loras"] = [
                {"model_name": l.model_name, "strength": l.strength}
                for l in compatible_loras
            ]

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/async/txt2img",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()

        return data.get("task_id", "")

    async def img2img_async(
        self,
        init_image_url: str,
        prompt: str,
        negative_prompt: Optional[str] = None,
        strength: float = 0.7,
        width: int = 1024,
        height: int = 1024,
        model: Optional[str] = None,
        steps: int = 20,
        guidance_scale: float = 7.5,
        seed: int = -1,
        image_num: int = 1,
        sampler_name: str = "DPM++ 2M",
        loras: Optional[list[LoRAConfig]] = None,
        ip_adapters: Optional[list[IPAdapterConfig]] = None,
        controlnet: Optional[ControlNetConfig] = None,
    ) -> str:
        import httpx
        
        image_base64 = await self._download_image_base64(init_image_url)
        
        resolved_model = await self._get_img2img_model(model)
        resolved_strength = await self._get_img2img_strength(strength)
        resolved_sampler = await self._get_img2img_sampler(sampler_name)
        resolved_width = await self._get_image_width(width)
        resolved_height = await self._get_image_height(height)
        resolved_steps = await self._get_image_steps(steps)
        resolved_cfg = await self._get_image_cfg(guidance_scale)
        
        payload = {
            "extra": await _apply_novita_webhook({"response_image_type": "jpeg"}),
            "request": {
                "model_name": resolved_model,
                "image_base64": image_base64,
                "prompt": prompt,
                "negative_prompt": negative_prompt or self.DEFAULT_NEGATIVE_PROMPT,
                "width": resolved_width,
                "height": resolved_height,
                "image_num": image_num,
                "steps": resolved_steps,
                "seed": seed,
                "guidance_scale": resolved_cfg,
                "sampler_name": resolved_sampler,
                "strength": resolved_strength,
                "clip_skip": 1,
            }
        }
        
        compatible_loras = self._filter_sdxl_loras(loras)
        if compatible_loras:
            payload["request"]["loras"] = [
                {"model_name": l.model_name, "strength": l.strength}
                for l in compatible_loras
            ]

        if ip_adapters:
            resolved_ip_adapters = [
                IPAdapterConfig(
                    image_base64=ip.image_base64,
                    model_name=ip.model_name,
                    strength=await self._get_ip_adapter_strength(ip.strength),
                )
                for ip in ip_adapters
            ]
            payload["request"]["ip_adapters"] = [
                {
                    "model_name": ip.model_name,
                    "image_base64": ip.image_base64,
                    "strength": ip.strength
                }
                for ip in resolved_ip_adapters
            ]
        
        if controlnet:
            resolved_controlnet_strength = await self._get_openpose_strength(controlnet.strength)
            payload["request"]["controlnet"] = {
                "units": [{
                    "model_name": controlnet.model_name,
                    "image_base64": controlnet.image_base64,
                    "strength": resolved_controlnet_strength,
                    "preprocessor": controlnet.preprocessor or "dwpose",
                    "guidance_start": controlnet.guidance_start,
                    "guidance_end": controlnet.guidance_end,
                }]
            }
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/async/img2img",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            if response.is_error:
                response_text = response.text[:2000]
                logger.error(
                    "Novita img2img rejected request: status=%s body=%s model=%s "
                    "size=%sx%s has_controlnet=%s has_ip_adapters=%s has_loras=%s",
                    response.status_code,
                    response_text,
                    resolved_model,
                    resolved_width,
                    resolved_height,
                    bool(controlnet),
                    bool(ip_adapters),
                    bool(compatible_loras),
                )
                raise httpx.HTTPStatusError(
                    f"Novita img2img failed with {response.status_code}: {response_text}",
                    request=response.request,
                    response=response,
                )
            data = response.json()
        
        return data.get("task_id", "")
    
    async def generate_with_ip_adapter(
        self,
        prompt: str,
        face_image_url: str,
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 768,
        ip_adapter_strength: float = 0.8,
        model: Optional[str] = None,
        steps: int = 25,
        guidance_scale: float = 7.0,
        seed: int = -1,
    ) -> str:
        import httpx
        
        face_base64 = await self._download_image_base64(face_image_url)
        
        payload = {
            "extra": {"response_image_type": "jpeg"},
            "request": {
                "model_name": model or self.DEFAULT_MODEL,
                "prompt": prompt,
                "negative_prompt": negative_prompt or self.DEFAULT_NEGATIVE_PROMPT,
                "width": width,
                "height": height,
                "image_num": 1,
                "steps": steps,
                "seed": seed,
                "guidance_scale": guidance_scale,
                "sampler_name": "DPM++ 2M",
                "clip_skip": 1,
                "ip_adapters": [{
                    "model_name": "ip-adapter_sdxl.bin",
                    "image_base64": face_base64,
                    "strength": ip_adapter_strength,
                }]
            }
        }
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/async/txt2img",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        return data.get("task_id", "")

    async def merge_face(
        self,
        image_url: str,
        face_image_url: str,
        response_image_type: str = "jpeg",
    ) -> str:
        """Call Novita merge-face and return merged image URL."""
        import httpx

        async def _request(payload: dict[str, Any]) -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.base_url}/merge-face",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                return response.json()

        payload: dict[str, Any] = {
            "extra": {"response_image_type": response_image_type},
            "face_image_file": face_image_url,
            "image_file": image_url,
        }

        try:
            data = await _request(payload)
        except httpx.HTTPStatusError:
            # Some tenants/models require base64 image content for *_file fields.
            image_base64 = await self._download_image_base64(image_url)
            face_base64 = await self._download_image_base64(face_image_url)
            fallback_payload: dict[str, Any] = {
                "extra": {"response_image_type": response_image_type},
                "face_image_file": face_base64,
                "image_file": image_base64,
            }
            data = await _request(fallback_payload)

        direct_url = data.get("image_url") or data.get("url")
        if isinstance(direct_url, str) and direct_url.strip():
            return direct_url.strip()

        images = data.get("images")
        if isinstance(images, list) and images:
            first = images[0] if isinstance(images[0], dict) else {}
            image_url_out = (
                first.get("image_url")
                or first.get("url")
                or first.get("data")
            )
            if isinstance(image_url_out, str) and image_url_out.strip():
                return image_url_out.strip()

        result_obj = data.get("result")
        if isinstance(result_obj, dict):
            image_url_out = (
                result_obj.get("image_url")
                or result_obj.get("url")
                or result_obj.get("data")
            )
            if isinstance(image_url_out, str) and image_url_out.strip():
                return image_url_out.strip()

        task_id = data.get("task_id")
        if isinstance(task_id, str) and task_id.strip():
            task_result = await self.wait_for_task(task_id.strip(), timeout_seconds=180)
            if task_result.image_url:
                return task_result.image_url
            raise ValueError(f"merge-face task finished without image (task_id={task_id})")

        raise ValueError("merge-face response did not contain an image URL")
    
    async def get_task_result(self, task_id: str) -> TaskResult:
        import httpx

        data: dict[str, Any] | None = None
        last_exc: Exception | None = None
        for attempt in range(3):
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    response = await client.get(
                        f"{self.base_url}/async/task-result",
                        params={"task_id": task_id},
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )
                    response.raise_for_status()
                    data = response.json()
                break
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                last_exc = e
                if status_code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))
            except httpx.RequestError as e:
                last_exc = e
                if attempt == 2:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))

        if data is None:
            raise RuntimeError(f"Empty task-result response for {task_id}: {last_exc}")

        task = data.get("task", {})
        status = (
            task.get("status")
            or data.get("status")
            or data.get("task_status")
            or "TASK_STATUS_QUEUED"
        )

        progress = task.get("progress_percent")
        if progress is None:
            progress = data.get("progress_percent")
        if progress is None:
            progress = data.get("progress")
        if progress is None:
            progress = 0.0

        reason = task.get("reason") or data.get("reason") or data.get("error")

        result = TaskResult(
            task_id=task_id,
            status=status,
            progress=progress,
            error=reason,
        )

        if status == "TASK_STATUS_SUCCEED":
            images = data.get("images", [])
            if images:
                first_image = images[0] or {}
                result.image_url = (
                    first_image.get("image_url")
                    or first_image.get("url")
                    or first_image.get("data")
                )

            if not result.image_url:
                result_obj = data.get("result", {})
                if isinstance(result_obj, dict):
                    result.image_url = (
                        result_obj.get("image_url")
                        or result_obj.get("url")
                        or result_obj.get("data")
                    )

            if not result.image_url:
                result.image_url = data.get("image_url") or data.get("url")

            videos = data.get("videos", [])
            if videos:
                result.video_url = videos[0].get("video_url")
            extra = data.get("extra", {})
            if extra.get("seed"):
                try:
                    result.seed = int(extra["seed"])
                except (ValueError, TypeError):
                    pass
        
        return result
    
    async def wait_for_task(
        self,
        task_id: str,
        timeout_seconds: int = 300,
        poll_interval: float = 2.0,
    ) -> TaskResult:
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            result = await self.get_task_result(task_id)
            
            if result.status in ("TASK_STATUS_SUCCEED", "TASK_STATUS_FAILED"):
                return result
            
            await asyncio.sleep(poll_interval)
        
        return TaskResult(
            task_id=task_id,
            status="TASK_STATUS_FAILED",
            error="Timeout waiting for task result",
        )
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        model: str = "juggernautXL_juggXIByRundiffusion_148819.safetensors",
        steps: int = 20,
        cfg_scale: float = 7.0,
        seed: Optional[int] = None,
        **kwargs
    ) -> ImageGenerationResult:
        task_id = await self.txt2img_async(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            model=model,
            steps=steps,
            guidance_scale=cfg_scale,
            seed=seed or -1,
        )
        
        result = await self.wait_for_task(task_id)
        
        if result.status != "TASK_STATUS_SUCCEED":
            raise Exception(f"Image generation failed: {result.error or 'Unknown error'}")
        
        return ImageGenerationResult(
            image_url=result.image_url or "",
            seed=result.seed,
            width=width,
            height=height,
            task_id=task_id,
        )
    
    async def img2img(
        self,
        init_image: str,
        prompt: str,
        strength: float = 0.7,
        **kwargs
    ) -> ImageGenerationResult:
        task_id = await self.img2img_async(
            init_image_url=init_image,
            prompt=prompt,
            strength=strength,
        )
        
        result = await self.wait_for_task(task_id)
        
        if result.status != "TASK_STATUS_SUCCEED":
            raise Exception(f"Image generation failed: {result.error or 'Unknown error'}")
        
        return ImageGenerationResult(
            image_url=result.image_url or "",
            seed=result.seed,
            task_id=task_id,
        )



class ZImageTurboLoraProvider(NovitaImageProvider):
    """Novita Z Image Turbo LoRA — faster generation, simpler payload, no model selection."""

    ENDPOINT = "/async/z-image-turbo-lora"

    @staticmethod
    def _resolve_lora_path(model_name: str) -> str:
        """Convert a civitai shorthand to a direct download URL.

        Novita's z-image-turbo-lora endpoint rejects the `civitai:MID@VID`
        shorthand with `failed to exec task`. It accepts HTTPS URLs pointing
        at civitai's model download API. Anything else (URLs, Novita-native
        names) is passed through unchanged.
        """
        if model_name.startswith("civitai:") and "@" in model_name:
            version_id = model_name.split("@", 1)[1]
            return f"https://civitai.com/api/download/models/{version_id}"
        return model_name

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
        image_num: int = 1,
        sampler_name: str = "DPM++ 2M",
        loras: Optional[list[LoRAConfig]] = None,
        restore_faces: bool = False,
    ) -> str:
        import httpx

        resolved_width = await self._get_image_width(width)
        resolved_height = await self._get_image_height(height)

        payload: dict[str, Any] = {
            "extra": await _apply_novita_webhook({}),
            "prompt": prompt,
            "seed": seed,
            "size": f"{resolved_width}*{resolved_height}",
        }
        if loras:
            payload["loras"] = [
                {"path": self._resolve_lora_path(l.model_name), "scale": l.strength}
                for l in loras
            ]

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}{self.ENDPOINT}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return data.get("task_id", "")


class NovitaVideoProvider(BaseMediaProvider):
    # WAN 2.1 i2v: no model_name in payload; image passed as image_url (not base64)
    # Docs: https://novita.ai/docs/api-reference/model-apis-wan-i2v

    async def generate_video_async(
        self,
        prompt: str,
        init_image: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        width: int = 832,
        height: int = 480,
        steps: int = 30,
        guidance_scale: float = 5.0,
        flow_shift: float = 5.0,
        seed: int = -1,
        enable_safety_checker: bool = False,
        loras: Optional[list[LoRAConfig]] = None,
        fast_mode: Optional[bool] = None,
        **kwargs,
    ) -> str:
        import httpx

        endpoint = "/async/wan-i2v" if init_image else "/async/wan-t2v"

        payload: dict[str, Any] = {
            "extra": await _apply_novita_webhook({}),
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "guidance_scale": guidance_scale,
            "flow_shift": flow_shift,
            "seed": seed,
            "enable_safety_checker": enable_safety_checker,
        }
        if init_image:
            payload["image_url"] = init_image
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if loras:
            payload["loras"] = [
                {"path": ZImageTurboLoraProvider._resolve_lora_path(l.model_name), "scale": l.strength}
                for l in loras
            ]
        if fast_mode is not None:
            payload["fast_mode"] = fast_mode

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}{endpoint}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        return data.get("task_id", "")

    async def get_task_result(self, task_id: str) -> TaskResult:
        import httpx

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{self.base_url}/async/task-result",
                params={"task_id": task_id},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            response.raise_for_status()
            data = response.json()

        task = data.get("task", {})
        status = task.get("status", "TASK_STATUS_QUEUED")

        result = TaskResult(
            task_id=task_id,
            status=status,
            progress=task.get("progress_percent", 0.0),
            error=task.get("reason"),
        )

        if status == "TASK_STATUS_SUCCEED":
            videos = data.get("videos", [])
            if videos:
                result.video_url = videos[0].get("video_url")

        return result

    async def generate_video(
        self,
        prompt: str,
        init_image: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        width: int = 832,
        height: int = 480,
        steps: int = 30,
        guidance_scale: float = 5.0,
        flow_shift: float = 5.0,
        seed: int = -1,
        enable_safety_checker: bool = False,
        timeout_seconds: int = 600,
        loras: Optional[list[LoRAConfig]] = None,
        fast_mode: Optional[bool] = None,
        **kwargs,
    ) -> VideoGenerationResult:
        task_id = await self.generate_video_async(
            prompt=prompt,
            init_image=init_image,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            guidance_scale=guidance_scale,
            flow_shift=flow_shift,
            seed=seed,
            enable_safety_checker=enable_safety_checker,
            loras=loras,
            fast_mode=fast_mode,
        )

        result = await self.wait_for_task(task_id, timeout_seconds=timeout_seconds)

        if result.status != "TASK_STATUS_SUCCEED":
            raise Exception(f"Video generation failed: {result.error or 'Unknown error'}")

        return VideoGenerationResult(
            video_url=result.video_url or "",
            duration=None,
            task_id=task_id,
        )

    async def wait_for_task(
        self,
        task_id: str,
        timeout_seconds: int = 600,
        poll_interval: float = 5.0,
    ) -> TaskResult:
        import time
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            result = await self.get_task_result(task_id)

            if result.status in ("TASK_STATUS_SUCCEED", "TASK_STATUS_FAILED"):
                return result

            await asyncio.sleep(poll_interval)

        return TaskResult(
            task_id=task_id,
            status="TASK_STATUS_FAILED",
            error=f"Timeout after {timeout_seconds}s waiting for WAN2.1 task",
        )


class ElevenLabsProvider(BaseMediaProvider):
    async def generate_audio(
        self,
        text: str,
        voice_id: str,
        model_id: str = "eleven_v3",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        **kwargs
    ) -> AudioGenerationResult:
        import httpx
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "model_id": model_id,
                    "voice_settings": {
                        "stability": stability,
                        "similarity_boost": similarity_boost
                    }
                }
            )
            response.raise_for_status()
        
        return AudioGenerationResult(
            audio_url="",
            voice_id=voice_id
        )
    
    async def get_voices(self) -> list[dict]:
        import httpx
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                f"{self.base_url}/voices",
                headers={"xi-api-key": self.api_key}
            )
            response.raise_for_status()
            data = response.json()
        
        return data.get("voices", [])
