import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.config import settings
from app.database import SessionLocal
from app.models import Account
from app.scheduler.pipeline import PipelineOrchestrator

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def scheduled_scan_job():
    """Periodic job scanning all registered active cloud accounts."""
    db = SessionLocal()
    try:
        accounts = db.query(Account).filter(Account.is_active == True).all()
        logger.info(f"Triggering scheduled CloudOptima scan across {len(accounts)} active accounts...")
        for acc in accounts:
            try:
                PipelineOrchestrator.run_pipeline_for_account(db, acc)
            except Exception as e:
                logger.error(f"Error scanning account {acc.account_id}: {e}")
    finally:
        db.close()

def start_scheduler():
    """Starts the background scan scheduler."""
    if not scheduler.running:
        scheduler.add_job(
            func=scheduled_scan_job,
            trigger=IntervalTrigger(minutes=settings.SCAN_INTERVAL_MINUTES),
            id="cloudoptima_scan_job",
            name="Periodic Multi-Cloud Waste & Risk Scan",
            replace_existing=True
        )
        scheduler.start()
        logger.info(f"Background scan scheduler started (Interval: {settings.SCAN_INTERVAL_MINUTES} mins).")

def stop_scheduler():
    """Stops the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scan scheduler stopped.")
