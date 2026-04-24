import logging
from typing import Optional
from ..core.config import get_settings
from .config_service import ConfigService
from .media import NovitaImageProvider, NovitaVideoProvider, ZImageTurboLoraProvider, ElevenLabsProvider

logger = logging.getLogger(__name__)

NOVITA_DEFAULT_BASE_URL = "https://api.novita.ai/v3"
ELEVENLABS_DEFAULT_BASE_URL = "https://api.elevenlabs.io/v1"


class MediaService:
    _instance = None

    def __init__(self):
        self.settings = get_settings()
        self._image_providers = {}
        self._video_providers = {}
        self._audio_providers = {}

    @classmethod
    def get_instance(cls) -> "MediaService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def refresh_providers(self) -> None:
        config_svc = ConfigService()
        novita_key = await config_svc.get_config_value("NOVITA_API_KEY") or self.settings.novita_api_key
        raw_novita_base_url = await config_svc.get_config_value("NOVITA_BASE_URL") or NOVITA_DEFAULT_BASE_URL
        novita_base_url = self._normalize_novita_base_url(raw_novita_base_url)
        el_api_key = await config_svc.get_config_value("ELEVENLABS_API_KEY") or self.settings.elevenlabs_api_key
        el_base_url = await config_svc.get_config_value("ELEVENLABS_BASE_URL") or ELEVENLABS_DEFAULT_BASE_URL

        if str(raw_novita_base_url).rstrip("/") != novita_base_url:
            logger.warning(
                "NOVITA_BASE_URL normalized from '%s' to '%s' for async media endpoints",
                raw_novita_base_url,
                novita_base_url,
            )
        logger.info(f"MediaService refreshing: novita_base_url={novita_base_url}")

        new_image: dict = {}
        new_video: dict = {}
        new_audio: dict = {}
        if novita_key:
            new_image["novita"] = NovitaImageProvider(api_key=novita_key, base_url=novita_base_url)
            new_image["z_image_turbo_lora"] = ZImageTurboLoraProvider(api_key=novita_key, base_url=novita_base_url)
            new_video["novita"] = NovitaVideoProvider(api_key=novita_key, base_url=novita_base_url)
        if el_api_key:
            new_audio["elevenlabs"] = ElevenLabsProvider(api_key=el_api_key, base_url=el_base_url)
        self._image_providers = new_image
        self._video_providers = new_video
        self._audio_providers = new_audio
        logger.info("MediaService providers refreshed from config")

    @staticmethod
    def _normalize_novita_base_url(base_url: str) -> str:
        normalized = (base_url or "").strip().rstrip("/")
        if not normalized:
            return NOVITA_DEFAULT_BASE_URL
        if normalized.startswith("https://api.novita.ai") or normalized.startswith("http://api.novita.ai"):
            if normalized.endswith("/v3"):
                return normalized
            if normalized.endswith("/openai/v1"):
                return normalized[: -len("/openai/v1")] + "/v3"
            if normalized.endswith("/openai"):
                return normalized[: -len("/openai")] + "/v3"
            if normalized.endswith("api.novita.ai"):
                return normalized + "/v3"
        return normalized

    def get_image_provider(self, name: Optional[str] = None) -> Optional[NovitaImageProvider]:
        if name:
            return self._image_providers.get(name)
        return next(iter(self._image_providers.values()), None)
    
    def get_video_provider(self, name: Optional[str] = None) -> Optional[NovitaVideoProvider]:
        if name:
            return self._video_providers.get(name)
        return next(iter(self._video_providers.values()), None)
    
    def get_audio_provider(self, name: Optional[str] = None) -> Optional[ElevenLabsProvider]:
        if name:
            return self._audio_providers.get(name)
        return next(iter(self._audio_providers.values()), None)
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: int = 512,
        height: int = 512,
        provider: Optional[str] = None,
        **kwargs
    ):
        prov = self.get_image_provider(provider)
        if not prov:
            raise ValueError(f"Image provider {provider} not available")
        
        try:
            return await prov.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Primary provider failed: {e}")
            
            for alt_name, alt_prov in self._image_providers.items():
                if alt_name != provider:
                    try:
                        logger.info(f"Trying fallback provider: {alt_name}")
                        return await alt_prov.generate_image(
                            prompt=prompt,
                            negative_prompt=negative_prompt,
                            width=width,
                            height=height,
                            **kwargs
                        )
                    except Exception:
                        continue
            
            raise
    
    async def generate_video(
        self,
        prompt: str,
        init_image: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ):
        prov = self.get_video_provider(provider)
        if not prov:
            raise ValueError(f"Video provider {provider} not available")
        
        return await prov.generate_video(
            prompt=prompt,
            init_image=init_image,
            **kwargs
        )
    
    async def generate_audio(
        self,
        text: str,
        voice_id: str,
        provider: Optional[str] = None,
        **kwargs
    ):
        prov = self.get_audio_provider(provider)
        if not prov:
            raise ValueError(f"Audio provider {provider} not available")
        
        return await prov.generate_audio(
            text=text,
            voice_id=voice_id,
            **kwargs
        )
    
    async def health_check(self) -> dict:
        results = {"image": {}, "video": {}, "audio": {}}
        
        for name, prov in self._image_providers.items():
            results["image"][name] = await prov.health_check()
        
        for name, prov in self._video_providers.items():
            results["video"][name] = await prov.health_check()
        
        for name, prov in self._audio_providers.items():
            results["audio"][name] = await prov.health_check()
        
        return results
