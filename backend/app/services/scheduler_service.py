import logging
from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .database_service import DatabaseService
from .credit_service import credit_service

logger = logging.getLogger(__name__)

scheduler: Optional[AsyncIOScheduler] = None


async def check_subscription_expiry():
    logger.info("Running subscription expiry check...")
    
    db = DatabaseService()
    
    try:
        with db.get_session() as session:
            from ..models.user import User
            
            expired_users = session.query(User).filter(
                User.tier != "free",
                User.subscription_end_date != None,
                User.subscription_end_date < datetime.utcnow()
            ).all()
            
            for user in expired_users:
                user.tier = "free"
                user.subscription_end_date = None
                user.subscription_period = None
                logger.info(f"User {user.id} subscription expired, downgraded to free")
            
            if expired_users:
                session.commit()
                logger.info(f"Downgraded {len(expired_users)} expired subscribers")
            else:
                logger.info("No expired subscriptions found")
                
    except Exception as e:
        logger.error(f"Error checking subscription expiry: {e}")


async def grant_monthly_credits_job():
    logger.info("Running monthly credits grant...")
    
    db = DatabaseService()
    
    try:
        with db.get_session() as session:
            from ..models.user import User
            
            subscribers = session.query(User).filter(
                User.tier == "premium",
                User.subscription_end_date != None,
                User.subscription_end_date > datetime.utcnow()
            ).all()
            
            granted_count = 0
            
            for user in subscribers:
                if user.last_monthly_credit_grant:
                    last_grant = user.last_monthly_credit_grant
                    if datetime.utcnow() - last_grant < timedelta(days=28):
                        continue
                
                try:
                    await credit_service.grant_monthly_credits(user.id)
                    granted_count += 1
                except Exception as e:
                    logger.error(f"Failed to grant monthly credits to user {user.id}: {e}")
            
            logger.info(f"Granted monthly credits to {granted_count} subscribers")
            
    except Exception as e:
        logger.error(f"Error granting monthly credits: {e}")


async def cleanup_expired_orders():
    logger.info("Running expired orders cleanup...")
    
    from .redis_service import RedisService
    redis = RedisService()
    
    try:
        pass
    except Exception as e:
        logger.error(f"Error cleaning up expired orders: {e}")


async def fetch_google_trends():
    logger.info("Running Google Trends fetch...")
    
    try:
        from .trend_service import trend_service
        result = await trend_service.refresh_trends()
        logger.info(f"Google Trends fetch result: {result}")
    except Exception as e:
        logger.error(f"Error fetching Google Trends: {e}")


async def rebuild_user_preference_profiles():
    logger.info("Running user preference profile rebuild...")
    
    try:
        from .user_preference_service import user_preference_service
        from app.core.database import db
        
        rows = await db.execute("SELECT id FROM users", fetch_all=True)
        if not rows:
            logger.info("No users found for preference rebuild")
            return
        
        rebuilt = 0
        for row in rows:
            try:
                profile = await user_preference_service.build_user_profile(row["id"])
                if profile:
                    rebuilt += 1
            except Exception as e:
                logger.error(f"Error rebuilding profile for user {row['id']}: {e}")
        
        logger.info(f"Rebuilt {rebuilt}/{len(rows)} user preference profiles")
    except Exception as e:
        logger.error(f"Error rebuilding user preference profiles: {e}")


async def analyze_character_performance():
    logger.info("Running character performance analysis...")
    
    try:
        from .performance_analyzer import performance_analyzer
        analysis = await performance_analyzer.analyze_top_performers(days=30)
        updated = await performance_analyzer.update_generation_weights(analysis)
        logger.info(f"Performance analysis complete, updated {updated} generation weights")
    except Exception as e:
        logger.error(f"Error analyzing character performance: {e}")


async def record_daily_performance():
    logger.info("Running daily performance recording...")
    
    try:
        from .performance_analyzer import performance_analyzer
        await performance_analyzer.record_daily_performance()
        logger.info("Daily performance recording complete")
    except Exception as e:
        logger.error(f"Error recording daily performance: {e}")


def init_scheduler():
    global scheduler
    
    if scheduler is not None:
        logger.warning("Scheduler already initialized")
        return scheduler
    
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(
        check_subscription_expiry,
        trigger=IntervalTrigger(hours=6),
        id="check_subscription_expiry",
        name="Check Subscription Expiry",
        replace_existing=True,
    )
    
    scheduler.add_job(
        grant_monthly_credits_job,
        trigger=CronTrigger(hour=2, minute=0),
        id="grant_monthly_credits",
        name="Grant Monthly Credits",
        replace_existing=True,
    )
    
    scheduler.add_job(
        cleanup_expired_orders,
        trigger=IntervalTrigger(hours=24),
        id="cleanup_expired_orders",
        name="Cleanup Expired Orders",
        replace_existing=True,
    )
    
    scheduler.add_job(
        fetch_google_trends,
        trigger=CronTrigger(hour=3, minute=0),
        id="fetch_google_trends",
        name="Fetch Google Trends",
        replace_existing=True,
    )
    
    scheduler.add_job(
        rebuild_user_preference_profiles,
        trigger=CronTrigger(hour=5, minute=0),
        id="rebuild_user_preference_profiles",
        name="Rebuild User Preference Profiles",
        replace_existing=True,
    )
    
    scheduler.add_job(
        analyze_character_performance,
        trigger=CronTrigger(hour=4, minute=0),
        id="analyze_character_performance",
        name="Analyze Character Performance",
        replace_existing=True,
    )
    
    scheduler.add_job(
        record_daily_performance,
        trigger=CronTrigger(hour=1, minute=0),
        id="record_daily_performance",
        name="Record Daily Performance",
        replace_existing=True,
    )
    
    logger.info("Scheduler initialized with jobs: check_subscription_expiry, grant_monthly_credits, cleanup_expired_orders, fetch_google_trends, rebuild_user_preference_profiles, analyze_character_performance, record_daily_performance")
    
    return scheduler


def start_scheduler():
    global scheduler
    
    if scheduler is None:
        init_scheduler()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")
    else:
        logger.warning("Scheduler already running")


def shutdown_scheduler():
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shutdown")
