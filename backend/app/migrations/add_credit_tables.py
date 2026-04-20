"""
Database migration script for Credit system.

Run this script to add new credit-related tables and columns.

Usage:
    python -m app.migrations.add_credit_tables
"""

import asyncio
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    from app.core.database import db
    
    logger.info("Starting credit system migration...")
    
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
    
    new_columns = {
        "user_type": "VARCHAR(20) DEFAULT 'free'",
        "purchased_credits": "REAL DEFAULT 0.0",
        "monthly_credits": "REAL DEFAULT 0.0",
        "subscription_period": "VARCHAR(10)",
        "subscription_start_date": "DATETIME",
        "subscription_end_date": "DATETIME",
        "last_monthly_credit_grant": "DATETIME",
        "signup_bonus_granted": "BOOLEAN DEFAULT 0",
    }
    
    for col_name, col_type in new_columns.items():
        if col_name not in columns:
            await session.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
            logger.info(f"Added column {col_name} to users table")
    
    if "credits" in columns:
        try:
            await session.execute(text("ALTER TABLE users RENAME COLUMN credits TO credits_old"))
            await session.execute(text("ALTER TABLE users ADD COLUMN credits REAL DEFAULT 0.0"))
            await session.execute(text("UPDATE users SET credits = CAST(credits_old AS REAL)"))
            await session.execute(text("ALTER TABLE users DROP COLUMN credits_old"))
            logger.info("Converted credits column to REAL")
        except Exception as e:
            logger.warning(f"Could not convert credits column: {e}")
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS credit_cost_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_cost REAL DEFAULT 0.1,
            voice_cost REAL DEFAULT 0.2,
            image_cost INTEGER DEFAULT 2,
            video_cost INTEGER DEFAULT 4,
            voice_call_per_minute INTEGER DEFAULT 3,
            signup_bonus_credits INTEGER DEFAULT 10,
            premium_monthly_credits INTEGER DEFAULT 100,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_by VARCHAR(255)
        )
    """))
    logger.info("Created credit_cost_config table")
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS credit_packs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pack_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            credits INTEGER NOT NULL,
            price_cents INTEGER NOT NULL,
            bonus_credits INTEGER DEFAULT 0,
            is_popular BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            display_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    logger.info("Created credit_packs table")
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period VARCHAR(10) UNIQUE NOT NULL,
            price_cents INTEGER NOT NULL,
            monthly_equivalent_cents INTEGER NOT NULL,
            discount_percent INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            display_order INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    logger.info("Created subscription_plans table")
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_type VARCHAR(30) NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            usage_type VARCHAR(30),
            credit_source VARCHAR(20),
            order_id VARCHAR(100),
            character_id VARCHAR(100),
            session_id VARCHAR(100),
            description VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """))
    logger.info("Created credit_transactions table")
    
    await session.execute(text("CREATE INDEX IF NOT EXISTS ix_credit_transactions_user_id ON credit_transactions(user_id)"))
    await session.execute(text("CREATE INDEX IF NOT EXISTS ix_credit_transactions_created_at ON credit_transactions(created_at)"))
    
    await session.commit()


async def migrate_postgresql(session):
    logger.info("Running PostgreSQL migration...")
    
    result = await session.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'users'
    """))
    columns = [row[0] for row in result.fetchall()]
    
    new_columns = {
        "user_type": "VARCHAR(20) DEFAULT 'free'",
        "purchased_credits": "REAL DEFAULT 0.0",
        "monthly_credits": "REAL DEFAULT 0.0",
        "subscription_period": "VARCHAR(10)",
        "subscription_start_date": "TIMESTAMP",
        "subscription_end_date": "TIMESTAMP",
        "last_monthly_credit_grant": "TIMESTAMP",
        "signup_bonus_granted": "BOOLEAN DEFAULT FALSE",
    }
    
    for col_name, col_type in new_columns.items():
        if col_name not in columns:
            await session.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
            logger.info(f"Added column {col_name} to users table")
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS credit_cost_config (
            id SERIAL PRIMARY KEY,
            message_cost REAL DEFAULT 0.1,
            voice_cost REAL DEFAULT 0.2,
            image_cost INTEGER DEFAULT 2,
            video_cost INTEGER DEFAULT 4,
            voice_call_per_minute INTEGER DEFAULT 3,
            signup_bonus_credits INTEGER DEFAULT 10,
            premium_monthly_credits INTEGER DEFAULT 100,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by VARCHAR(255)
        )
    """))
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS credit_packs (
            id SERIAL PRIMARY KEY,
            pack_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            credits INTEGER NOT NULL,
            price_cents INTEGER NOT NULL,
            bonus_credits INTEGER DEFAULT 0,
            is_popular BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id SERIAL PRIMARY KEY,
            period VARCHAR(10) UNIQUE NOT NULL,
            price_cents INTEGER NOT NULL,
            monthly_equivalent_cents INTEGER NOT NULL,
            discount_percent INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            display_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS credit_transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            transaction_type VARCHAR(30) NOT NULL,
            amount REAL NOT NULL,
            balance_after REAL NOT NULL,
            usage_type VARCHAR(30),
            credit_source VARCHAR(20),
            order_id VARCHAR(100),
            character_id VARCHAR(100),
            session_id VARCHAR(100),
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    
    await session.execute(text("CREATE INDEX IF NOT EXISTS ix_credit_transactions_user_id ON credit_transactions(user_id)"))
    await session.execute(text("CREATE INDEX IF NOT EXISTS ix_credit_transactions_created_at ON credit_transactions(created_at)"))
    
    await session.commit()
    logger.info("PostgreSQL migration completed")


async def migrate_generic(session):
    logger.info("Running generic migration...")
    
    try:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS credit_cost_config (
                id INTEGER PRIMARY KEY,
                message_cost REAL DEFAULT 0.1,
                voice_cost REAL DEFAULT 0.2,
                image_cost INTEGER DEFAULT 2,
                video_cost INTEGER DEFAULT 4,
                voice_call_per_minute INTEGER DEFAULT 3,
                signup_bonus_credits INTEGER DEFAULT 10,
                premium_monthly_credits INTEGER DEFAULT 100,
                updated_at DATETIME,
                updated_by VARCHAR(255)
            )
        """))
        
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS credit_packs (
                id INTEGER PRIMARY KEY,
                pack_id VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(100) NOT NULL,
                credits INTEGER NOT NULL,
                price_cents INTEGER NOT NULL,
                bonus_credits INTEGER DEFAULT 0,
                is_popular BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
        
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS subscription_plans (
                id INTEGER PRIMARY KEY,
                period VARCHAR(10) UNIQUE NOT NULL,
                price_cents INTEGER NOT NULL,
                monthly_equivalent_cents INTEGER NOT NULL,
                discount_percent INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                display_order INTEGER DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
        
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS credit_transactions (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                transaction_type VARCHAR(30) NOT NULL,
                amount REAL NOT NULL,
                balance_after REAL NOT NULL,
                usage_type VARCHAR(30),
                credit_source VARCHAR(20),
                order_id VARCHAR(100),
                character_id VARCHAR(100),
                session_id VARCHAR(100),
                description VARCHAR(255),
                created_at DATETIME
            )
        """))
        
        await session.commit()
        logger.info("Generic migration completed")
        
    except Exception as e:
        logger.error(f"Generic migration failed: {e}")
        raise


async def seed_default_data():
    """Seed default credit packs and subscription plans."""
    from app.services.pricing_service import pricing_service
    
    logger.info("Seeding default data...")
    await pricing_service.initialize_default_data()
    logger.info("Default data seeded")


if __name__ == "__main__":
    asyncio.run(migrate())
    asyncio.run(seed_default_data())
