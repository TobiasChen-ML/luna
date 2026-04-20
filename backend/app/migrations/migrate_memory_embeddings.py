import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.core.database import db
from app.services.embedding_service import embedding_service
from app.services.vector_store import memory_vector_store, global_memory_vector_store

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_memory_embeddings(batch_size: int = 100):
    logger.info("Starting memory embedding migration...")
    
    total_count = await db.execute(
        "SELECT COUNT(*) as count FROM memories WHERE embedding IS NULL OR embedding = ''",
        fetch=True
    )
    total = total_count["count"] if total_count else 0
    logger.info(f"Found {total} memories without embeddings")
    
    offset = 0
    migrated = 0
    failed = 0
    
    while True:
        rows = await db.execute(
            """
            SELECT id, user_id, character_id, content, layer, importance
            FROM memories
            WHERE embedding IS NULL OR embedding = ''
            LIMIT ? OFFSET ?
            """,
            (batch_size, offset),
            fetch_all=True
        )
        
        if not rows:
            break
        
        for row in rows:
            try:
                embedding = await embedding_service.embed(row["content"])
                
                if embedding:
                    embedding_blob = bytes(
                        int(v * 10000) for v in embedding[:min(len(embedding), 100)]
                    )
                    
                    await db.execute(
                        "UPDATE memories SET embedding = ? WHERE id = ?",
                        (embedding_blob, row["id"])
                    )
                    
                    try:
                        await memory_vector_store.add_memory(
                            memory_id=row["id"],
                            embedding=embedding,
                            content=row["content"],
                            user_id=row["user_id"],
                            character_id=row["character_id"],
                            layer=row["layer"],
                            importance=row["importance"],
                        )
                    except Exception as ve:
                        logger.warning(f"Vector store add failed for {row['id']}: {ve}")
                    
                    migrated += 1
                    
                    if migrated % 50 == 0:
                        logger.info(f"Progress: {migrated}/{total}")
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Failed to migrate memory {row['id']}: {e}")
                failed += 1
        
        offset += batch_size
    
    logger.info(f"Migration complete: {migrated} migrated, {failed} failed")
    return {"migrated": migrated, "failed": failed}


async def migrate_global_memory_embeddings(batch_size: int = 50):
    logger.info("Starting global memory embedding migration...")
    
    total_count = await db.execute(
        "SELECT COUNT(*) as count FROM global_memories",
        fetch=True
    )
    total = total_count["count"] if total_count else 0
    logger.info(f"Found {total} global memories")
    
    offset = 0
    migrated = 0
    failed = 0
    
    while True:
        rows = await db.execute(
            """
            SELECT id, user_id, content, category
            FROM global_memories
            LIMIT ? OFFSET ?
            """,
            (batch_size, offset),
            fetch_all=True
        )
        
        if not rows:
            break
        
        for row in rows:
            try:
                embedding = await embedding_service.embed(row["content"])
                
                if embedding:
                    try:
                        await global_memory_vector_store.add_global_memory(
                            memory_id=row["id"],
                            embedding=embedding,
                            content=row["content"],
                            user_id=row["user_id"],
                            category=row["category"],
                        )
                    except Exception as ve:
                        logger.warning(f"Vector store add failed for {row['id']}: {ve}")
                    
                    migrated += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.error(f"Failed to migrate global memory {row['id']}: {e}")
                failed += 1
        
        offset += batch_size
    
    logger.info(f"Global memory migration complete: {migrated} migrated, {failed} failed")
    return {"migrated": migrated, "failed": failed}


async def rebuild_vector_store():
    logger.info("Rebuilding vector store from scratch...")
    
    try:
        await memory_vector_store.clear()
        logger.info("Cleared memories collection")
    except Exception as e:
        logger.warning(f"Could not clear memories collection: {e}")
    
    try:
        await global_memory_vector_store.clear()
        logger.info("Cleared global_memories collection")
    except Exception as e:
        logger.warning(f"Could not clear global_memories collection: {e}")
    
    await migrate_memory_embeddings()
    await migrate_global_memory_embeddings()
    
    logger.info("Vector store rebuild complete")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate memory embeddings to vector store")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild vector store from scratch")
    parser.add_argument("--global-only", action="store_true", help="Only migrate global memories")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for migration")
    
    args = parser.parse_args()
    
    try:
        await db.connect()
        
        if args.rebuild:
            await rebuild_vector_store()
        elif args.global_only:
            await migrate_global_memory_embeddings(args.batch_size)
        else:
            await migrate_memory_embeddings(args.batch_size)
            
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
