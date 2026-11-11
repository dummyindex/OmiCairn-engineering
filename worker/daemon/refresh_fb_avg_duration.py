import os
import requests
import logging
import time
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(
    level=logging.INFO,
    format="<FB Average Duration Daemon> %(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("FB Average Duration Daemon")


def refresh_fb_avg_duration():
    try:
        logger.info("Refreshing function block average durations")
        url = "http://localhost:80/interval/refresh-fb-avg-duration"
        requests.post(url)
        logger.info("Refreshing function block average durations done")
    except Exception as e:
        logger.error(
            f"Failed to refresh function block average durations: {e}")


def check_server_inited():
    try:
        url = "http://localhost:80/health/check"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def scheduled_refresh_fb_avg_duration():
    """Scheduled job: refresh Function Block average execution duration"""
    try:
        logger.info("[Scheduled Task] Refreshing FB average duration triggered")
        refresh_fb_avg_duration()
    except Exception as e:
        logger.error(f"[Scheduled Task] Failed to refresh FB average duration: {e}", exc_info=True)


def main():
    logger.info("FB Average Duration Daemon starting...")
    
    # Wait for the Flask server to start
    logger.info("Waiting for Flask server to initialize...")
    time.sleep(50)
    
    retry_count = 0
    max_retries = 60  # Retry at most 60 times (5 minutes total)
    
    while not check_server_inited():
        logger.info(f"Waiting for server to be initialized (attempt {retry_count + 1}/{max_retries})")
        time.sleep(5)
        retry_count += 1
        
        if retry_count >= max_retries:
            logger.error("Server failed to initialize after 5 minutes. Exiting.")
            sys.exit(1)
    
    logger.info("Server initialized successfully")
    
    # Run one refresh immediately on startup
    logger.info("Running initial FB average duration refresh...")
    refresh_fb_avg_duration()
    
    # Create the scheduler
    logger.info("=" * 60)
    logger.info("Initializing APScheduler for periodic FB average duration refresh:")
    logger.info("  - Interval: every 4 hours")
    logger.info("=" * 60)
    
    scheduler = BlockingScheduler(
        timezone=os.environ.get('SCHEDULER_TIMEZONE', 'UTC'),
        job_defaults={
            'coalesce': True,  # Merge missed runs
            'max_instances': 1,  # At most one running instance per job
            'misfire_grace_time': 300  # Grace period for a missed run (5 minutes)
        }
    )
    
    # Add the scheduled job (every 4 hours)
    scheduler.add_job(
        func=scheduled_refresh_fb_avg_duration,
        trigger=IntervalTrigger(hours=4),
        id='refresh_fb_avg_duration',
        name='Refresh FB Average Duration',
        replace_existing=True
    )
    logger.info("✓ Added FB average duration refresh job (every 4 hours)")
    
    # Start the scheduler (blocking)
    try:
        logger.info("=" * 60)
        logger.info("APScheduler started successfully")
        logger.info("FB Average Duration Daemon is now running...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("FB Average Duration Daemon stopped by user")
        scheduler.shutdown(wait=False)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        scheduler.shutdown(wait=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
