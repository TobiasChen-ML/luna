"""
Database migration: add story_plus and creator subscription tiers.

Existing 'premium' users are kept as-is; the billing system maps 'premium' to
story_plus feature access so no data mutation is needed.

Usage:
    python -m app.migrations.add_subscription_tiers_v2
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NEW_PLANS = [
    # (period, tier_id, price_cents, monthly_equivalent_cents, discount_percent, monthly_credits, display_order)
    ("story_plus_month", "story_plus", 999, 999, 0, 150, 10),
    ("story_plus_year", "story_plus", 3596, 300, 70, 150, 11),
    ("creator_month", "creator", 1999, 1999, 0, 300, 20),
    ("creator_year", "creator", 7196, 600, 70, 300, 21),
]


async def migrate():
    from app.core.database import db

    logger.info("Adding story_plus and creator subscription plans...")

    # Check if subscription_plans table has a tier_id column; add if missing.
    try:
        await db.execute("ALTER TABLE subscription_plans ADD COLUMN tier_id TEXT")
        logger.info("Column tier_id added to subscription_plans.")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            logger.info("Column tier_id already exists.")
        else:
            logger.warning(f"tier_id column skipped: {e}")

    try:
        await db.execute("ALTER TABLE subscription_plans ADD COLUMN monthly_credits INTEGER DEFAULT 100")
        logger.info("Column monthly_credits added to subscription_plans.")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            logger.info("Column monthly_credits already exists.")
        else:
            logger.warning(f"monthly_credits column skipped: {e}")

    for period, tier_id, price_cents, monthly_equivalent_cents, discount_percent, monthly_credits, display_order in NEW_PLANS:
        existing = await db.execute(
            "SELECT id FROM subscription_plans WHERE period = ?",
            (period,),
            fetch=True,
        )
        if existing:
            logger.info(f"Plan '{period}' already exists, skipping.")
            continue
        try:
            await db.execute(
                """
                INSERT INTO subscription_plans
                    (period, tier_id, price_cents, monthly_equivalent_cents,
                     discount_percent, monthly_credits, display_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    period,
                    tier_id,
                    price_cents,
                    monthly_equivalent_cents,
                    discount_percent,
                    monthly_credits,
                    display_order,
                ),
            )
            logger.info(f"Inserted plan: {period} (tier={tier_id}, ${price_cents/100:.2f})")
        except Exception as e:
            logger.error(f"Failed to insert plan {period}: {e}")

    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate())
