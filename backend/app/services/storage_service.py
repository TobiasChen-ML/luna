import logging
import uuid
import httpx
import boto3
from botocore.exceptions import ClientError
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class StorageService:
    _instance = None

    def __init__(self):
        self.settings = get_settings()
        self._s3 = None
        self._bucket_name = None
        self._public_url = None

    @classmethod
    def get_instance(cls) -> "StorageService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _init_client(self):
        if self._s3 is not None:
            return

        storage_config = await self._get_storage_config()
        access_key = storage_config.get("r2_access_key_id")
        secret_key = storage_config.get("r2_secret_access_key")
        self._bucket_name = storage_config.get("r2_bucket_name", "aigirl-media")
        endpoint_url = storage_config.get("r2_endpoint_url")
        self._public_url = storage_config.get("r2_public_url", "")

        self._s3 = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )

    async def _get_storage_config(self) -> dict:
        from app.core.config import get_storage_config
        return await get_storage_config()

    async def upload_from_url(
        self,
        source_url: str,
        folder: str = "characters",
        filename: Optional[str] = None,
    ) -> str:
        await self._init_client()

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(source_url)
            response.raise_for_status()
            content = response.content

        if filename is None:
            ext = self._get_extension(source_url) or ".jpg"
            filename = f"{uuid.uuid4().hex}{ext}"

        return self._put_object(content, folder, filename, self._get_content_type(filename))

    async def upload_bytes(
        self,
        content: bytes,
        folder: str = "characters",
        filename: Optional[str] = None,
        content_type: str = "image/jpeg",
    ) -> str:
        await self._init_client()

        if filename is None:
            ext = self._get_extension_from_content_type(content_type) or ".bin"
            filename = f"{uuid.uuid4().hex}{ext}"

        return self._put_object(content, folder, filename, content_type)

    def _put_object(self, content: bytes, folder: str, filename: str, content_type: str) -> str:
        key = f"{folder}/{filename}"
        try:
            self._s3.put_object(
                Bucket=self._bucket_name,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
        except ClientError as e:
            logger.error(f"R2 upload failed for key {key}: {e}")
            raise

        public_url = f"{self._public_url}/{key}"
        if not public_url.startswith(("http://", "https://")):
            logger.error(f"Storage public_url missing protocol: {public_url}")
            raise RuntimeError(f"R2_PUBLIC_URL is not configured or invalid (got: {self._public_url!r})")
        logger.info(f"Uploaded to R2: {public_url}")
        return public_url

    def _get_extension(self, url: str) -> str:
        from urllib.parse import urlparse
        path = urlparse(url).path
        if "." in path:
            return "." + path.rsplit(".", 1)[-1].lower()
        return ".jpg"

    def _get_content_type(self, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        content_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "mp4": "video/mp4",
            "webm": "video/webm",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
        }
        return content_types.get(ext, "application/octet-stream")

    def _get_extension_from_content_type(self, content_type: str) -> str:
        extensions = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "video/mp4": ".mp4",
            "video/webm": ".webm",
            "audio/mpeg": ".mp3",
            "audio/wav": ".wav",
        }
        return extensions.get(content_type, ".bin")


storage_service = StorageService()
