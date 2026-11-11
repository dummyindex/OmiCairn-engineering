import os
import requests
import logging
import time
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(
    level=logging.INFO,
    format="<Jobs Moniter Deamon> %(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("Jobs Monitor Deamon")


def init():
    try:
        logger.info("Initializing")
        url = "http://localhost:80/interval/init"
        requests.get(url)
        logger.info("Initializing done")
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")


def scan_timeout_computations():
    try:
        logger.info("Scanning timeout computations")
        url = "http://localhost:80/interval/scan-timeout"
        requests.get(url)
        logger.info("Scanning timeout computations done")
    except Exception as e:
        logger.error(f"Failed to scan timeout computations: {e}")


def scan_omissive_computations():
    try:
        logger.info("Scanning omissive computations")
        url = "http://localhost:80/interval/scan-omissive"
        requests.get(url)
        logger.info("Scanning omissive computations done")
    except Exception as e:
        logger.error(f"Failed to scan omissive computations: {e}")


def unlock_nodes_interval():
    try:
        logger.info("Unlocking nodes interval")
        url = "http://localhost:80/interval/unlock-nodes-interval"
        requests.post(url)
        logger.info("Unlocking nodes interval done")
    except Exception as e:
        logger.error(f"Failed to unlock nodes interval: {e}")


def check_server_inited():
    try:
        url = "http://localhost:80/health/check"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def scheduled_scan_timeout_computations():
    """Scheduled job: scan timed-out computations"""
    try:
        logger.info("[Scheduled Task] Scanning timeout computations triggered")
        scan_timeout_computations()
    except Exception as e:
        logger.error(f"[Scheduled Task] Failed to scan timeout computations: {e}", exc_info=True)


def scheduled_unlock_nodes():
    """Scheduled job: unlock nodes"""
    try:
        logger.info("[Scheduled Task] Unlocking nodes triggered")
        unlock_nodes_interval()
    except Exception as e:
        logger.error(f"[Scheduled Task] Failed to unlock nodes: {e}", exc_info=True)


def main():
    logger.info("Jobs Monitor Daemon starting...")
    
    # Wait for the Flask server to start
    logger.info("Waiting for Flask server to initialize...")
    time.sleep(5)
    
    retry_count = 0
    max_retries = 60  # Retry at most 60 times (5 minutes total)
    
    while not check_server_inited():
        logger.info(f"Waiting for server to be inited (attempt {retry_count + 1}/{max_retries})")
        time.sleep(5)
        retry_count += 1
        
        if retry_count >= max_retries:
            logger.error("Server failed to initialize after 5 minutes. Exiting.")
            sys.exit(1)
    
    logger.info("Server inited successfully")
    
    # Initialization and first scan
    logger.info("Running initialization...")
    init()
    
    logger.info("Running initial scan for omissive computations...")
    scan_omissive_computations()
    
    time.sleep(5)
    
    # Create the scheduler
    logger.info("=" * 60)
    logger.info("Initializing APScheduler for periodic job monitoring:")
    logger.info("  - Scan timeout computations: every 5 minutes")
    logger.info("  - Unlock nodes: every 7 seconds")
    logger.info("=" * 60)
    
    scheduler = BlockingScheduler(
        timezone=os.environ.get('SCHEDULER_TIMEZONE', 'UTC'),
        job_defaults={
            'coalesce': True,  # Merge missed runs
            'max_instances': 1,  # At most one running instance per job
            'misfire_grace_time': 60  # Grace period for a missed run (1 minute)
        }
    )
    
    # Add the timeout-scan job (every 5 minutes)
    scheduler.add_job(
        func=scheduled_scan_timeout_computations,
        trigger=IntervalTrigger(minutes=5),
        id='scan_timeout_computations',
        name='Scan Timeout Computations',
        replace_existing=True
    )
    logger.info("✓ Added scan timeout computations job (every 5 minutes)")
    
    # Add the node-unlock job (every 7 seconds)
    scheduler.add_job(
        func=scheduled_unlock_nodes,
        trigger=IntervalTrigger(seconds=7),
        id='unlock_nodes',
        name='Unlock Nodes',
        replace_existing=True
    )
    logger.info("✓ Added unlock nodes job (every 7 seconds)")
    
    # Start the scheduler (blocking)
    try:
        logger.info("=" * 60)
        logger.info("APScheduler started successfully")
        logger.info("Jobs Monitor Daemon is now running...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Jobs Monitor Daemon stopped by user")
        scheduler.shutdown(wait=False)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        scheduler.shutdown(wait=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
