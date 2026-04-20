"""
Database migration script for Voice Management system.

Run this script to add voices table and update characters.voice_id relationship.

Usage:
    python -m app.migrations.add_voice_management_tables
"""

import asyncio
import logging
import uuid
import json
from datetime import datetime
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    from app.core.database import db
    
    logger.info("Starting voice management migration...")
    
    async with db.get_session() as session:
        try:
            dialect = session.bind.dialect.name
            
            if dialect == "sqlite":
                await migrate_sqlite(session)
            elif dialect == "postgresql":
                await migrate_postgresql(session)
            else:
                logger.warning(f"Unknown dialect: {dialect}, attempting generic migration")
                await migrate_generic(session)
            
            await seed_default_voices(session)
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise


async def migrate_sqlite(session):
    logger.info("Running SQLite migration...")
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS voices (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            display_name TEXT,
            description TEXT,
            preview_url TEXT,
            provider TEXT NOT NULL DEFAULT 'elevenlabs',
            provider_voice_id TEXT NOT NULL,
            model_id TEXT,
            language TEXT DEFAULT 'en',
            gender TEXT DEFAULT 'female',
            tone TEXT,
            settings TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            usage_count INTEGER DEFAULT 0,
            last_used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    logger.info("Created voices table")
    
    await session.execute(text("CREATE INDEX IF NOT EXISTS idx_voices_provider ON voices(provider)"))
    await session.execute(text("CREATE INDEX IF NOT EXISTS idx_voices_language ON voices(language)"))
    await session.execute(text("CREATE INDEX IF NOT EXISTS idx_voices_is_active ON voices(is_active)"))
    
    await session.commit()


async def migrate_postgresql(session):
    logger.info("Running PostgreSQL migration...")
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS voices (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            display_name VARCHAR(100),
            description TEXT,
            preview_url TEXT,
            provider VARCHAR(20) NOT NULL DEFAULT 'elevenlabs',
            provider_voice_id VARCHAR(100) NOT NULL,
            model_id VARCHAR(50),
            language VARCHAR(10) DEFAULT 'en',
            gender VARCHAR(10) DEFAULT 'female',
            tone VARCHAR(30),
            settings TEXT DEFAULT '{}',
            is_active BOOLEAN DEFAULT TRUE,
            usage_count INTEGER DEFAULT 0,
            last_used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    await session.execute(text("CREATE INDEX IF NOT EXISTS idx_voices_provider ON voices(provider)"))
    await session.execute(text("CREATE INDEX IF NOT EXISTS idx_voices_language ON voices(language)"))
    await session.execute(text("CREATE INDEX IF NOT EXISTS idx_voices_is_active ON voices(is_active)"))
    
    await session.commit()
    logger.info("PostgreSQL migration completed")


async def migrate_generic(session):
    logger.info("Running generic migration...")
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS voices (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            display_name VARCHAR(100),
            description TEXT,
            preview_url TEXT,
            provider VARCHAR(20) NOT NULL DEFAULT 'elevenlabs',
            provider_voice_id VARCHAR(100) NOT NULL,
            model_id VARCHAR(50),
            language VARCHAR(10) DEFAULT 'en',
            gender VARCHAR(10) DEFAULT 'female',
            tone VARCHAR(30),
            settings TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            usage_count INTEGER DEFAULT 0,
            last_used_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    await session.commit()
    logger.info("Generic migration completed")


async def seed_default_voices(session):
    logger.info("Seeding default voices...")
    
    default_voices = [
        {
            "id": "voice_el_rachel",
            "name": "Rachel",
            "display_name": "Rachel (ElevenLabs)",
            "description": "Warm, friendly American female voice",
            "provider": "elevenlabs",
            "provider_voice_id": "21m00Tcm4TlvDq8ikWAM",
            "model_id": "eleven_multilingual_v2",
            "language": "en",
            "gender": "female",
            "tone": "warm",
            "settings": json.dumps({"stability": 0.5, "similarity_boost": 0.75})
        },
        {
            "id": "voice_el_domi",
            "name": "Domi",
            "display_name": "Domi (ElevenLabs)",
            "description": "Edgy, seductive female voice",
            "provider": "elevenlabs",
            "provider_voice_id": "AZGtz5r1OBiYb8W5hBMT",
            "model_id": "eleven_multilingual_v2",
            "language": "en",
            "gender": "female",
            "tone": "seductive",
            "settings": json.dumps({"stability": 0.4, "similarity_boost": 0.85})
        },
        {
            "id": "voice_el_bella",
            "name": "Bella",
            "display_name": "Bella (ElevenLabs)",
            "description": "Soft, feminine voice perfect for ASMR",
            "provider": "elevenlabs",
            "provider_voice_id": "EXAVITQu4vrWxn9f3VRE",
            "model_id": "eleven_multilingual_v2",
            "language": "en",
            "gender": "female",
            "tone": "asmr",
            "settings": json.dumps({"stability": 0.6, "similarity_boost": 0.8})
        },
        {
            "id": "voice_el_adam",
            "name": "Adam",
            "display_name": "Adam (ElevenLabs)",
            "description": "Deep, calm male voice",
            "provider": "elevenlabs",
            "provider_voice_id": "pNInz6obpgDQGcFmaJgB",
            "model_id": "eleven_multilingual_v2",
            "language": "en",
            "gender": "male",
            "tone": "calm",
            "settings": json.dumps({"stability": 0.5, "similarity_boost": 0.75})
        },
        {
            "id": "voice_el_antoni",
            "name": "Antoni",
            "display_name": "Antoni (ElevenLabs)",
            "description": "Young, energetic male voice",
            "provider": "elevenlabs",
            "provider_voice_id": "ErXwobaYiN0xxP1Y8z2O",
            "model_id": "eleven_multilingual_v2",
            "language": "en",
            "gender": "male",
            "tone": "lively",
            "settings": json.dumps({"stability": 0.45, "similarity_boost": 0.8})
        },
        {
            "id": "voice_ds_zhixiaoxia",
            "name": "知小夏",
            "display_name": "知小夏 (通义千问)",
            "description": "甜美温柔的中文女声",
            "provider": "dashscope",
            "provider_voice_id": "zhixiaoxia",
            "language": "zh",
            "gender": "female",
            "tone": "sweet",
            "settings": json.dumps({"speed": 1.0, "pitch": 0})
        },
        {
            "id": "voice_ds_zhichu",
            "name": "知楚",
            "display_name": "知楚 (通义千问)",
            "description": "成熟稳重的中文女声",
            "provider": "dashscope",
            "provider_voice_id": "zhichu",
            "language": "zh",
            "gender": "female",
            "tone": "mature",
            "settings": json.dumps({"speed": 0.9, "pitch": -2})
        },
        {
            "id": "voice_ds_zhiyan",
            "name": "知燕",
            "display_name": "知燕 (通义千问)",
            "description": "知性优雅的中文女声",
            "provider": "dashscope",
            "provider_voice_id": "zhiyan",
            "language": "zh",
            "gender": "female",
            "tone": "elegant",
            "settings": json.dumps({"speed": 1.0, "pitch": 0})
        },
        {
            "id": "voice_ds_zhimiao",
            "name": "知妙",
            "display_name": "知妙 (通义千问)",
            "description": "活泼可爱的中文女声",
            "provider": "dashscope",
            "provider_voice_id": "zhimiao",
            "language": "zh",
            "gender": "female",
            "tone": "lively",
            "settings": json.dumps({"speed": 1.1, "pitch": 2})
        },
        {
            "id": "voice_ds_zhiying",
            "name": "知英",
            "display_name": "知英 (通义千问)",
            "description": "沉稳有力的中文男声",
            "provider": "dashscope",
            "provider_voice_id": "zhiying",
            "language": "zh",
            "gender": "male",
            "tone": "calm",
            "settings": json.dumps({"speed": 1.0, "pitch": -3})
        },
    ]
    
    for voice_data in default_voices:
        existing = await session.execute(
            text("SELECT id FROM voices WHERE id = :id"),
            {"id": voice_data["id"]}
        )
        if existing.fetchone() is None:
            await session.execute(
                text("""
                    INSERT INTO voices (
                        id, name, display_name, description, preview_url,
                        provider, provider_voice_id, model_id, language, gender,
                        tone, settings, is_active, usage_count, created_at, updated_at
                    ) VALUES (
                        :id, :name, :display_name, :description, :preview_url,
                        :provider, :provider_voice_id, :model_id, :language, :gender,
                        :tone, :settings, 1, 0, :created_at, :updated_at
                    )
                """),
                {
                    **voice_data,
                    "preview_url": None,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
            )
            logger.info(f"Inserted voice: {voice_data['name']}")
    
    await session.commit()
    logger.info("Default voices seeded")


if __name__ == "__main__":
    asyncio.run(migrate())