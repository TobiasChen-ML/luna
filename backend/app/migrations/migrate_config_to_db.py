"""
Migration: Move config from Redis to database

Usage: python -m app.migrations.migrate_config_to_db
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import db


async def create_config_table():
    await db.connect()
    await db.execute("""
        CREATE TABLE IF NOT EXISTS app_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            is_secret INTEGER DEFAULT 0,
            updated_by TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


async def migrate_redis_to_db():
    from app.services.config_service import ConfigService
    config_service = ConfigService()
    count = await config_service.migrate_from_redis()
    print(f"Migrated {count} config values from Redis to database")
    return count


async def init_defaults():
    from app.services.config_service import ConfigService
    config_service = ConfigService()
    count = await config_service.init_defaults()
    print(f"Initialized {count} default config values")
    return count


async def main():
    print("Creating config table...")
    await create_config_table()
    
    print("Migrating from Redis...")
    await migrate_redis_to_db()
    
    print("Initializing defaults...")
    await init_defaults()
    
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())