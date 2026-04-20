"""
Database migration script for Group Chat support.

Adds participants column to chat_sessions and speaker_id to chat_messages.

Usage:
    python -m app.migrations.add_group_chat_support
"""

import asyncio
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    from app.core.database import db
    
    logger.info("Starting group chat support migration...")
    
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
    
    result = await session.execute(text("PRAGMA table_info(chat_sessions)"))
    session_columns = [row[1] for row in result.fetchall()]
    
    if "participants" not in session_columns:
        await session.execute(text("ALTER TABLE chat_sessions ADD COLUMN participants TEXT"))
        logger.info("Added participants column to chat_sessions table")
    
    result = await session.execute(text("PRAGMA table_info(chat_messages)"))
    message_columns = [row[1] for row in result.fetchall()]
    
    if "speaker_id" not in message_columns:
        await session.execute(text("ALTER TABLE chat_messages ADD COLUMN speaker_id TEXT"))
        logger.info("Added speaker_id column to chat_messages table")
    
    await session.commit()
    logger.info("SQLite migration completed")


async def migrate_postgresql(session):
    logger.info("Running PostgreSQL migration...")
    
    result = await session.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'chat_sessions'
    """))
    session_columns = [row[0] for row in result.fetchall()]
    
    if "participants" not in session_columns:
        await session.execute(text("ALTER TABLE chat_sessions ADD COLUMN participants TEXT"))
        logger.info("Added participants column to chat_sessions table")
    
    result = await session.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'chat_messages'
    """))
    message_columns = [row[0] for row in result.fetchall()]
    
    if "speaker_id" not in message_columns:
        await session.execute(text("ALTER TABLE chat_messages ADD COLUMN speaker_id TEXT"))
        logger.info("Added speaker_id column to chat_messages table")
    
    await session.commit()
    logger.info("PostgreSQL migration completed")


async def migrate_generic(session):
    logger.info("Running generic migration...")
    
    try:
        await session.execute(text("ALTER TABLE chat_sessions ADD COLUMN participants TEXT"))
        logger.info("Added participants column to chat_sessions table")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            logger.info("participants column already exists in chat_sessions")
        else:
            raise
    
    try:
        await session.execute(text("ALTER TABLE chat_messages ADD COLUMN speaker_id TEXT"))
        logger.info("Added speaker_id column to chat_messages table")
    except Exception as e:
        if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
            logger.info("speaker_id column already exists in chat_messages")
        else:
            raise
    
    await session.commit()
    logger.info("Generic migration completed")


if __name__ == "__main__":
    asyncio.run(migrate())
