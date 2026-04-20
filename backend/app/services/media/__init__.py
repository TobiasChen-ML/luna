import logging
import base64
import asyncio
from typing import Optional, Any
from dataclasses import dataclass, field
from app.core.config import get_settings

logger = logging.getLogger(__name__)


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
    strength: float = 0.8
    model_name: str = "ip-adapter_sd15.bin"


@dataclass
class ControlNetConfig:
    model_name: str
    image_base64: str
    strength: float = 1.0
    preprocessor: Optional[str] = None


class BaseMediaProvider:
    def __init__(self, api_key: str, base_url: str, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
    
    async def health_check(self) -> bool:
        return True
    
    async def _download_image_base64(self, image_url: str) -> str:
        import httpx
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            return base64.b64encode(response.content).decode("utf-8")


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
        return 0.7
    
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
            "extra": {"response_image_type": "jpeg"},
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
        
        if loras:
            payload["request"]["loras"] = [
                {"model_name": l.model_name, "strength": l.strength}
                for l in loras
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
            "extra": {"response_image_type": "jpeg"},
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
        
        if loras:
            payload["request"]["loras"] = [
                {"model_name": l.model_name, "strength": l.strength}
                for l in loras
            ]
        
        if ip_adapters:
            payload["request"]["ip_adapters"] = [
                {
                    "model_name": ip.model_name,
                    "image_base64": ip.image_base64,
                    "strength": ip.strength
                }
                for ip in ip_adapters
            ]
        
        if controlnet:
            payload["request"]["controlnet"] = {
                "units": [{
                    "model_name": controlnet.model_name,
                    "image_base64": controlnet.image_base64,
                    "strength": controlnet.strength,
                    "preprocessor": controlnet.preprocessor or "openpose",
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
            response.raise_for_status()
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
                "model_name": model or self.DEFAULT_MODEL_SD15,
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
                    "model_name": "ip-adapter_sd15.bin",
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
    
    async def get_task_result(self, task_id: str) -> TaskResult:
        import httpx
        
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(
                f"{self.base_url}/async/task-result",
                params={"task_id": task_id},
                headers={"Authorization": f"Bearer {self.api_key}"}
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
            images = data.get("images", [])
            if images:
                result.image_url = images[0].get("image_url")
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

    ENDPOINT = "/v3/async/z-image-turbo-lora"

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
            "prompt": prompt,
            "seed": seed,
            "size": f"{resolved_width}*{resolved_height}",
        }
        if loras:
            payload["loras"] = [
                {"path": l.model_name, "scale": l.strength}
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
        **kwargs,
    ) -> str:
        import httpx

        endpoint = "/v3/async/wan-i2v" if init_image else "/v3/async/wan-t2v"

        payload: dict[str, Any] = {
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
