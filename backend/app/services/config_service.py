import logging
from typing import Optional, Any
from cryptography.fernet import Fernet
from ..core.database import db
from ..models.config import (
    ConfigGroup,
    CONFIG_DEFINITIONS,
)

logger = logging.getLogger(__name__)

ENCRYPTION_KEY_ENV = "CONFIG_ENCRYPTION_KEY"


class ConfigService:
    def __init__(self):
        self._fernet: Optional[Fernet] = None
        self._encryption_key: Optional[str] = None

    def _get_encryption_key(self) -> Optional[str]:
        import os
        if self._encryption_key is None:
            self._encryption_key = os.environ.get(ENCRYPTION_KEY_ENV)
        return self._encryption_key

    def _get_fernet(self) -> Optional[Fernet]:
        if self._fernet is None:
            key = self._get_encryption_key()
            if key:
                try:
                    self._fernet = Fernet(key.encode())
                except Exception as e:
                    logger.error(f"Failed to initialize Fernet: {e}")
        return self._fernet

    def _encrypt(self, value: str) -> str:
        fernet = self._get_fernet()
        if fernet:
            return fernet.encrypt(value.encode()).decode()
        return value

    def _decrypt(self, value: str) -> str:
        fernet = self._get_fernet()
        if fernet:
            try:
                return fernet.decrypt(value.encode()).decode()
            except Exception:
                return value
        return value

    def _mask_value(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        if len(value) <= 8:
            return "****"
        return value[:4] + "****" + value[-4:]

    def _is_secret_key(self, key: str) -> bool:
        for group_def in CONFIG_DEFINITIONS:
            for field in group_def.fields:
                if field.key == key:
                    return field.secret
        return False

    async def _db_get(self, key: str) -> Optional[str]:
        row = await db.execute(
            "SELECT value, is_secret FROM app_config WHERE key = ?",
            (key,),
            fetch=True
        )
        if row:
            value = row["value"]
            if row["is_secret"]:
                return self._decrypt(value)
            return value
        return None

    async def _db_set(self, key: str, value: str, is_secret: bool = False) -> bool:
        import os
        from datetime import datetime
        encrypted_value = self._encrypt(value) if is_secret else value
        now = datetime.utcnow().isoformat()
        await db.execute(
            """INSERT INTO app_config (key, value, is_secret, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET
               value = excluded.value,
               is_secret = excluded.is_secret,
               updated_at = excluded.updated_at""",
            (key, encrypted_value, 1 if is_secret else 0, now)
        )
        return True

    async def _db_delete(self, key: str) -> bool:
        await db.execute("DELETE FROM app_config WHERE key = ?", (key,))
        return True

    async def get_all_configs(self) -> dict[ConfigGroup, dict[str, Any]]:
        result: dict[ConfigGroup, dict[str, Any]] = {}
        for group_def in CONFIG_DEFINITIONS:
            group_data = {
                "group": group_def.group.value,
                "label": group_def.label,
                "description": group_def.description,
                "fields": [],
            }
            for field in group_def.fields:
                stored_value = await self._db_get(field.key)
                display_value = None
                if stored_value:
                    if field.secret:
                        display_value = self._mask_value(stored_value)
                    else:
                        display_value = stored_value
                elif field.default:
                    display_value = field.default
                group_data["fields"].append({
                    "key": field.key,
                    "label": field.label,
                    "type": field.type,
                    "placeholder": field.placeholder,
                    "default": field.default,
                    "required": field.required,
                    "secret": field.secret,
                    "description": field.description,
                    "value": display_value,
                    "options": field.options,
                    "model_provider": field.model_provider,
                })
            result[group_def.group] = group_data
        return result

    async def get_config_by_group(self, group: ConfigGroup) -> dict[str, Any]:
        for group_def in CONFIG_DEFINITIONS:
            if group_def.group == group:
                group_data = {
                    "group": group_def.group.value,
                    "label": group_def.label,
                    "description": group_def.description,
                    "fields": [],
                }
                for field in group_def.fields:
                    stored_value = await self._db_get(field.key)
                    display_value = None
                    if stored_value:
                        if field.secret:
                            display_value = self._mask_value(stored_value)
                        else:
                            display_value = stored_value
                    elif field.default:
                        display_value = field.default
                    group_data["fields"].append({
                        "key": field.key,
                        "label": field.label,
                        "type": field.type,
                        "placeholder": field.placeholder,
                        "default": field.default,
                        "required": field.required,
                        "secret": field.secret,
                        "description": field.description,
                        "value": display_value,
                        "options": field.options,
                        "model_provider": field.model_provider,
                    })
                return group_data
        return {}

    async def update_config_group(
        self, group: ConfigGroup, values: dict[str, str]
    ) -> dict[str, Any]:
        updated = []
        for group_def in CONFIG_DEFINITIONS:
            if group_def.group == group:
                for field in group_def.fields:
                    if field.key in values:
                        new_value = values[field.key]
                        if new_value is None:
                            continue
                        await self._db_set(field.key, str(new_value), field.secret)
                        updated.append(field.key)
        return {"updated": updated, "count": len(updated)}

    async def get_config_value(self, key: str) -> Optional[str]:
        return await self._db_get(key)

    async def set_config_value(self, key: str, value: str) -> bool:
        is_secret = self._is_secret_key(key)
        return await self._db_set(key, value, is_secret)

    async def delete_config_value(self, key: str) -> bool:
        return await self._db_delete(key)

    async def get_config_values_batch(self, keys: list[str]) -> dict[str, Optional[str]]:
        result = {}
        for key in keys:
            result[key] = await self.get_config_value(key)
        return result

    async def init_defaults(self) -> int:
        count = 0
        try:
            for group_def in CONFIG_DEFINITIONS:
                for field in group_def.fields:
                    if field.default:
                        existing = await self._db_get(field.key)
                        if not existing:
                            await self._db_set(field.key, field.default, field.secret)
                            count += 1
        except Exception as e:
            logger.warning(f"Failed to init defaults: {e}")
        return count

    def get_group_definitions(self) -> list[dict[str, Any]]:
        result = []
        for group_def in CONFIG_DEFINITIONS:
            result.append({
                "group": group_def.group.value,
                "label": group_def.label,
                "description": group_def.description,
                "fields": [
                    {
                        "key": f.key,
                        "label": f.label,
                        "type": f.type,
                        "placeholder": f.placeholder,
                        "default": f.default,
                        "required": f.required,
                        "secret": f.secret,
                        "description": f.description,
                        "options": f.options,
                        "model_provider": f.model_provider,
                    }
                    for f in group_def.fields
                ],
            })
        return result

    async def migrate_from_redis(self) -> int:
        try:
            from .redis_service import RedisService
            redis = RedisService()
            count = 0
            for group_def in CONFIG_DEFINITIONS:
                for field in group_def.fields:
                    redis_key = f"config:{field.key}"
                    try:
                        redis_value = await redis.get(redis_key)
                        if redis_value:
                            if field.secret:
                                try:
                                    decrypted = self._decrypt(redis_value)
                                    await self._db_set(field.key, decrypted, True)
                                except Exception:
                                    await self._db_set(field.key, redis_value, True)
                            else:
                                await self._db_set(field.key, redis_value, False)
                            await redis.delete(redis_key)
                            count += 1
                    except Exception as e:
                        logger.warning(f"Failed to migrate {field.key}: {e}")
            logger.info(f"Migrated {count} config values from Redis to database")
            return count
        except Exception as e:
            logger.error(f"Redis migration failed: {e}")
            return 0