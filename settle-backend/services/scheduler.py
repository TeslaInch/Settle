from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()


def start_scheduler():
    """Start the background scheduler."""
    if not scheduler.running:
        scheduler.start()


def stop_scheduler():
    """Stop the background scheduler."""
    if scheduler.running:
        scheduler.shutdown()


def add_job(func, trigger, **kwargs):
    """Add a job to the scheduler."""
    scheduler.add_job(func, trigger, **kwargs)


def remove_job(job_id: str):
    """Remove a job from the scheduler."""
    scheduler.remove_job(job_id)
