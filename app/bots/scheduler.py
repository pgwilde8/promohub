from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.bots.outreach_bot import OutreachBot
from app.core.config import settings
import logging
import asyncio

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def get_db_session() -> Session:
    """Get database session for background tasks"""
    return SessionLocal()


async def run_outreach_bot():
    """Scheduled task to process new leads for outreach"""
    logger.info("Starting scheduled outreach bot run...")
    
    db = get_db_session()
    try:
        outreach_bot = OutreachBot(db)
        sent_count = await outreach_bot.process_new_leads(max_emails_per_run=20)
        logger.info(f"Outreach bot completed: {sent_count} emails sent")
    except Exception as e:
        logger.error(f"Outreach bot error: {str(e)}")
    finally:
        db.close()


async def run_content_bot():
    """Scheduled task to generate blog content"""
    logger.info("Starting scheduled content generation...")
    
    db = get_db_session()
    try:
        # Import here to avoid circular imports
        from app.bots.content_bot import ContentBot
        
        content_bot = ContentBot(db)
        post_created = await content_bot.generate_weekly_post()
        
        if post_created:
            logger.info("Content bot completed: New blog post created")
        else:
            logger.info("Content bot completed: No new post needed")
            
    except Exception as e:
        logger.error(f"Content bot error: {str(e)}")
    finally:
        db.close()


async def run_social_bot():
    """Scheduled task to post content to social media"""
    logger.info("Starting scheduled social media posting...")
    
    db = get_db_session()
    try:
        # Import here to avoid circular imports
        from app.bots.social_bot import SocialBot
        
        social_bot = SocialBot(db)
        posts_created = await social_bot.process_pending_content()
        logger.info(f"Social bot completed: {posts_created} posts created")
        
    except Exception as e:
        logger.error(f"Social bot error: {str(e)}")
    finally:
        db.close()


async def run_enrichment_bot():
    """Scheduled task to enrich leads with Hunter.io"""
    logger.info("Starting scheduled lead enrichment...")
    
    try:
        # Import here to avoid circular imports
        from app.services.enrichment_service import run_enrichment_job
        
        result = await run_enrichment_job()
        
        if "error" in result:
            logger.error(f"Enrichment job failed: {result['error']}")
        else:
            logger.info(f"Enrichment job completed: {result['enriched']} leads enriched out of {result['processed']} processed")
            
    except Exception as e:
        logger.error(f"Enrichment bot error: {str(e)}")


async def run_retarget_bot():
    """Scheduled task to check for retargeting opportunities"""
    logger.info("Starting scheduled retarget bot run...")
    
    db = get_db_session()
    try:
        # Import here to avoid circular imports
        from app.bots.retarget_bot import RetargetBot
        
        retarget_bot = RetargetBot(db)
        emails_sent = await retarget_bot.check_retarget_opportunities()
        logger.info(f"Retarget bot completed: {emails_sent} retarget emails sent")
        
    except Exception as e:
        logger.error(f"Retarget bot error: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """Start the background task scheduler"""
    logger.info("Starting PromoHub task scheduler...")
    
    # Outreach bot - runs every 2 hours during business hours
    scheduler.add_job(
        run_outreach_bot,
        trigger=CronTrigger(hour='9-17/2'),  # Every 2 hours from 9 AM to 5 PM
        id='outreach_bot',
        max_instances=1,
        replace_existing=True
    )
    
    # Content bot - runs weekly on Mondays at 8 AM
    scheduler.add_job(
        run_content_bot,
        trigger=CronTrigger(day_of_week='mon', hour=8, minute=0),
        id='content_bot',
        max_instances=1,
        replace_existing=True
    )
    
    # Social bot - runs daily at 10 AM and 2 PM
    scheduler.add_job(
        run_social_bot,
        trigger=CronTrigger(hour='10,14', minute=0),
        id='social_bot',
        max_instances=1,
        replace_existing=True
    )
    
    # Retarget bot - runs every 4 hours
    scheduler.add_job(
        run_retarget_bot,
        trigger=IntervalTrigger(hours=4),
        id='retarget_bot',
        max_instances=1,
        replace_existing=True
    )
    
    # Enrichment bot - runs every 30 minutes during business hours  
    scheduler.add_job(
        run_enrichment_bot,
        trigger=CronTrigger(hour='9-17/1', minute='*/30'),  # Every 30 minutes from 9 AM to 5 PM
        id='enrichment_bot',
        max_instances=1,
        replace_existing=True
    )
    
    # Health check - runs every minute (lightweight)
    scheduler.add_job(
        lambda: logger.info("Scheduler health check: OK"),
        trigger=IntervalTrigger(minutes=1),
        id='health_check',
        max_instances=1,
        replace_existing=True
    )
    
    try:
        scheduler.start()
        logger.info("✅ Task scheduler started successfully")
        
        # Print scheduled jobs
        for job in scheduler.get_jobs():
            logger.info(f"📅 Scheduled job: {job.id} - Next run: {job.next_run_time}")
            
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {str(e)}")


def shutdown_scheduler():
    """Shutdown the background task scheduler"""
    logger.info("Shutting down task scheduler...")
    
    try:
        scheduler.shutdown(wait=True)
        logger.info("✅ Task scheduler shut down successfully")
    except Exception as e:
        logger.error(f"❌ Error shutting down scheduler: {str(e)}")


# Manual trigger functions for testing/admin use
async def trigger_outreach_now():
    """Manually trigger outreach bot"""
    await run_outreach_bot()


async def trigger_content_now():
    """Manually trigger content bot"""
    await run_content_bot()


async def trigger_social_now():
    """Manually trigger social bot"""
    await run_social_bot()


async def trigger_retarget_now():
    """Manually trigger retarget bot"""
    await run_retarget_bot()


async def trigger_enrichment_now():
    """Manually trigger enrichment bot"""
    await run_enrichment_bot()


def get_scheduler_status():
    """Get current scheduler status"""
    if not scheduler.running:
        return {"status": "stopped", "jobs": []}
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else "Not scheduled",
            "trigger": str(job.trigger)
        })
    
    return {
        "status": "running",
        "job_count": len(jobs),
        "jobs": jobs
    }


# For development/testing - run a lightweight version
if settings.debug:
    def start_dev_scheduler():
        """Start a development-friendly scheduler with longer intervals"""
        logger.info("Starting development scheduler with extended intervals...")
        
        # Outreach bot - every 30 minutes in dev
        scheduler.add_job(
            run_outreach_bot,
            trigger=IntervalTrigger(minutes=30),
            id='dev_outreach_bot',
            max_instances=1,
            replace_existing=True
        )
        
        # Content bot - every 2 hours in dev  
        scheduler.add_job(
            run_content_bot,
            trigger=IntervalTrigger(hours=2),
            id='dev_content_bot',
            max_instances=1,
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("✅ Development scheduler started")