"""
Database migration script for prompt template Chinese descriptions.

Adds:
- description_zh column to prompt_templates table
- Populates default Chinese descriptions for existing templates

Usage:
    python -m app.migrations.add_prompt_description_zh
"""

import asyncio
import logging
import aiosqlite
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_DESCRIPTIONS_ZH = {
    "safety_rules": "安全规则与内容限制：定义禁止生成的内容类型（涉未成年、政治、极端暴力、违法、仇恨言论），规定违规时的响应协议",
    "script_instruction": "剧本/叙事系统指令：控制故事推进、节点转换、情感门槛检查和关系进阶逻辑",
    "world_setting": "世界设定与角色身份：定义故事背景、世界规则、角色身份和用户身份",
    "character_setting": "角色人设与性格：包含基本资料、性格描述、背景故事、说话风格示例和当前内心状态",
    "relationship_state": "用户与角色间的关系状态：包含关系阶段、亲密度/信任度/欲望/依赖度属性值，以及各阶段的行为指导",
    "memory_context": "记忆与历史上下文：包含重要回忆、用户相关事实、近期话题和当前情绪状态",
    "plot_context": "剧情与场景上下文：包含当前场景描述、叙事背景、故事进展、剧情节点、可能的结局和可选分支",
    "output_instruction": "输出格式与行为指令：规定语言要求、内容安全、回复格式（内心独白/动作/对话）和行为准则",
}


async def migrate():
    from app.core.config import settings

    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    logger.info(f"Starting prompt description_zh migration on {db_path}...")

    async with aiosqlite.connect(db_path) as db:
        try:
            await add_description_zh_column(db)
            await populate_default_descriptions(db)
            await db.commit()
            logger.info("Migration completed successfully!")
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise


async def add_description_zh_column(db: aiosqlite.Connection):
    cursor = await db.execute("PRAGMA table_info(prompt_templates)")
    columns = [row[1] for row in await cursor.fetchall()]

    if "description_zh" not in columns:
        await db.execute("ALTER TABLE prompt_templates ADD COLUMN description_zh TEXT")
        logger.info("Added column description_zh to prompt_templates table")
    else:
        logger.info("Column description_zh already exists, skipping")


async def populate_default_descriptions(db: aiosqlite.Connection):
    for name, desc_zh in DEFAULT_DESCRIPTIONS_ZH.items():
        cursor = await db.execute(
            "SELECT name FROM prompt_templates WHERE name = ? AND description_zh IS NULL",
            (name,),
        )
        row = await cursor.fetchone()
        if row:
            await db.execute(
                "UPDATE prompt_templates SET description_zh = ? WHERE name = ?",
                (desc_zh, name),
            )
            logger.info(f"Updated description_zh for template: {name}")


if __name__ == "__main__":
    asyncio.run(migrate())
