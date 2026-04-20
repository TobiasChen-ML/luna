"""
Database migration script for adding stripe_customer_id column.

Run this script to add stripe_customer_id column to users table.

Usage:
    python -m app.migrations.add_stripe_customer_id
"""

import asyncio
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    from app.core.database import db
    
    logger.info("Starting stripe_customer_id migration...")
    
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
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise


async def migrate_sqlite(session):
    logger.info("Running SQLite migration...")
    
    result = await session.execute(text("PRAGMA table_info(users)"))
    columns = [row[1] for row in result.fetchall()]
    
    if "stripe_customer_id" not in columns:
        logger.info("Adding stripe_customer_id column to users table...")
        await session.execute(text("ALTER TABLE users ADD COLUMN stripe_customer_id TEXT"))
        await session.commit()
        logger.info("stripe_customer_id column added successfully")
    else:
        logger.info("stripe_customer_id column already exists, skipping")


async def migrate_postgresql(session):
    logger.info("Running PostgreSQL migration...")
    
    result = await session.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'stripe_customer_id'
    """))
    
    if not result.fetchone():
        logger.info("Adding stripe_customer_id column to users table...")
        await session.execute(text("ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(128)"))
        await session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id ON users(stripe_customer_id)"))
        await session.commit()
        logger.info("stripe_customer_id column added successfully")
    else:
        logger.info("stripe_customer_id column already exists, skipping")


async def migrate_generic(session):
    logger.info("Running generic migration...")
    
    try:
        await session.execute(text("ALTER TABLE users ADD COLUMN stripe_customer_id VARCHAR(128)"))
        await session.commit()
        logger.info("stripe_customer_id column added successfully")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            logger.info("stripe_customer_id column already exists, skipping")
        else:
            raise


if __name__ == "__main__":
    asyncio.run(migrate())
