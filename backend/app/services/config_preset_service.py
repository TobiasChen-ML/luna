import json
import uuid
from typing import Optional, Any
from datetime import datetime

from app.core.database import db


IMAGE_PRESET_KEYS = [
    "IMAGE_PROVIDER",
    "IMAGE_TXT2IMG_MODEL",
    "IMAGE_IMG2IMG_MODEL",
    "IMAGE_DEFAULT_WIDTH",
    "IMAGE_DEFAULT_HEIGHT",
    "IMAGE_DEFAULT_STEPS",
    "IMAGE_DEFAULT_CFG",
    "IMG2IMG_STRENGTH",
    "IMG2IMG_SAMPLER",
]

VIDEO_PRESET_KEYS = [
    "VIDEO_PROVIDER",
    "VIDEO_MODEL",
]

BUILTIN_IMAGE_PRESETS = [
    {
        "name": "写实风格 (Realistic)",
        "config": {
            "IMAGE_PROVIDER": "novita",
            "IMAGE_TXT2IMG_MODEL": "juggernautXL_v9Rdphoto2Lightning_285361.safetensors",
            "IMAGE_IMG2IMG_MODEL": "juggernautXL_v9Rdphoto2Lightning_285361.safetensors",
            "IMAGE_DEFAULT_WIDTH": "1024",
            "IMAGE_DEFAULT_HEIGHT": "1024",
            "IMAGE_DEFAULT_STEPS": "20",
            "IMAGE_DEFAULT_CFG": "7.5",
            "IMG2IMG_STRENGTH": "0.7",
            "IMG2IMG_SAMPLER": "DPM++ 2M",
        },
    },
    {
        "name": "动漫风格 (Anime)",
        "config": {
            "IMAGE_PROVIDER": "novita",
            "IMAGE_TXT2IMG_MODEL": "animagineXLV31_v31_325600.safetensors",
            "IMAGE_IMG2IMG_MODEL": "animagineXLV31_v31_325600.safetensors",
            "IMAGE_DEFAULT_WIDTH": "1024",
            "IMAGE_DEFAULT_HEIGHT": "1024",
            "IMAGE_DEFAULT_STEPS": "20",
            "IMAGE_DEFAULT_CFG": "7.0",
            "IMG2IMG_STRENGTH": "0.65",
            "IMG2IMG_SAMPLER": "DPM++ 2M",
        },
    },
    {
        "name": "高质量 (High Quality)",
        "config": {
            "IMAGE_PROVIDER": "novita",
            "IMAGE_TXT2IMG_MODEL": "leosamsHelloworldXL_helloworldXL70_485879.safetensors",
            "IMAGE_IMG2IMG_MODEL": "leosamsHelloworldXL_helloworldXL70_485879.safetensors",
            "IMAGE_DEFAULT_WIDTH": "1024",
            "IMAGE_DEFAULT_HEIGHT": "1024",
            "IMAGE_DEFAULT_STEPS": "25",
            "IMAGE_DEFAULT_CFG": "7.5",
            "IMG2IMG_STRENGTH": "0.7",
            "IMG2IMG_SAMPLER": "DPM++ 2M",
        },
    },
    {
        "name": "快速生成 (Fast)",
        "config": {
            "IMAGE_PROVIDER": "novita",
            "IMAGE_TXT2IMG_MODEL": "sd_xl_base_1.0.safetensors",
            "IMAGE_IMG2IMG_MODEL": "sd_xl_base_1.0.safetensors",
            "IMAGE_DEFAULT_WIDTH": "1024",
            "IMAGE_DEFAULT_HEIGHT": "1024",
            "IMAGE_DEFAULT_STEPS": "12",
            "IMAGE_DEFAULT_CFG": "5.0",
            "IMG2IMG_STRENGTH": "0.6",
            "IMG2IMG_SAMPLER": "DPM++ 2M",
        },
    },
]

BUILTIN_VIDEO_PRESETS = [
    {
        "name": "图生视频 (Image to Video)",
        "config": {
            "VIDEO_PROVIDER": "novita",
            "VIDEO_MODEL": "wan_i2v_22",
        },
    },
]


class ConfigPresetService:
    async def list_presets(self, category: str) -> list[dict[str, Any]]:
        rows = await db.execute(
            "SELECT * FROM config_presets WHERE category = ? ORDER BY is_builtin DESC, name ASC",
            (category,),
            fetch_all=True,
        )
        return [self._row_to_dict(row) for row in rows]

    async def get_preset(self, preset_id: str) -> Optional[dict[str, Any]]:
        row = await db.execute(
            "SELECT * FROM config_presets WHERE id = ?",
            (preset_id,),
            fetch=True,
        )
        return self._row_to_dict(row) if row else None

    async def get_active_preset(self, category: str) -> Optional[dict[str, Any]]:
        row = await db.execute(
            "SELECT * FROM config_presets WHERE category = ? AND is_active = 1",
            (category,),
            fetch=True,
        )
        return self._row_to_dict(row) if row else None

    async def create_preset(
        self,
        name: str,
        category: str,
        config: dict[str, str],
        is_builtin: bool = False,
    ) -> dict[str, Any]:
        preset_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """
            INSERT INTO config_presets (id, name, category, config_json, is_active, is_builtin, created_at, updated_at)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?)
            """,
            (preset_id, name, category, json.dumps(config), 1 if is_builtin else 0, now, now),
        )
        
        return {
            "id": preset_id,
            "name": name,
            "category": category,
            "config": config,
            "is_active": False,
            "is_builtin": is_builtin,
        }

    async def activate_preset(self, preset_id: str, redis_client: Optional[Any] = None) -> bool:
        preset = await self.get_preset(preset_id)
        if not preset:
            return False
        
        category = preset["category"]
        
        await db.execute(
            "UPDATE config_presets SET is_active = 0 WHERE category = ?",
            (category,),
        )
        
        await db.execute(
            "UPDATE config_presets SET is_active = 1, updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), preset_id),
        )
        
        if redis_client:
            config = preset["config"]
            for key, value in config.items():
                await redis_client.set(f"config:{key}", value)
        
        return True

    async def delete_preset(self, preset_id: str) -> bool:
        preset = await self.get_preset(preset_id)
        if not preset:
            return False
        
        if preset["is_builtin"]:
            raise ValueError("Cannot delete builtin preset")
        
        await db.execute(
            "DELETE FROM config_presets WHERE id = ?",
            (preset_id,),
        )
        return True

    async def init_builtin_presets(self) -> int:
        count = 0
        
        for preset_data in BUILTIN_IMAGE_PRESETS:
            existing = await db.execute(
                "SELECT id FROM config_presets WHERE name = ? AND category = 'image'",
                (preset_data["name"],),
                fetch=True,
            )
            if not existing:
                await self.create_preset(
                    name=preset_data["name"],
                    category="image",
                    config=preset_data["config"],
                    is_builtin=True,
                )
                count += 1
        
        for preset_data in BUILTIN_VIDEO_PRESETS:
            existing = await db.execute(
                "SELECT id FROM config_presets WHERE name = ? AND category = 'video'",
                (preset_data["name"],),
                fetch=True,
            )
            if not existing:
                await self.create_preset(
                    name=preset_data["name"],
                    category="video",
                    config=preset_data["config"],
                    is_builtin=True,
                )
                count += 1
        
        first_image = await db.execute(
            "SELECT id FROM config_presets WHERE category = 'image' AND is_active = 1",
            (),
            fetch=True,
        )
        if not first_image:
            first_preset = await db.execute(
                "SELECT id FROM config_presets WHERE category = 'image' AND is_builtin = 1 LIMIT 1",
                (),
                fetch=True,
            )
            if first_preset:
                await db.execute(
                    "UPDATE config_presets SET is_active = 1 WHERE id = ?",
                    (first_preset["id"],),
                )
        
        first_video = await db.execute(
            "SELECT id FROM config_presets WHERE category = 'video' AND is_active = 1",
            (),
            fetch=True,
        )
        if not first_video:
            first_preset = await db.execute(
                "SELECT id FROM config_presets WHERE category = 'video' AND is_builtin = 1 LIMIT 1",
                (),
                fetch=True,
            )
            if first_preset:
                await db.execute(
                    "UPDATE config_presets SET is_active = 1 WHERE id = ?",
                    (first_preset["id"],),
                )
        
        return count

    def _row_to_dict(self, row: dict) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "category": row["category"],
            "config": json.loads(row["config_json"]) if row["config_json"] else {},
            "is_active": bool(row["is_active"]),
            "is_builtin": bool(row["is_builtin"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }


def get_preset_keys_for_category(category: str) -> list[str]:
    if category == "image":
        return IMAGE_PRESET_KEYS
    elif category == "video":
        return VIDEO_PRESET_KEYS
    return []
