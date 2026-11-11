"""
RAG Vector Store Sync Daemon
Standalone daemon that periodically syncs to the RAG vector stores:
1. Fix Experience (fix_description table) - updated every 30 minutes
2. Code Library (function_block_version_v1 table) - updated every hour

Uses APScheduler for reliable scheduled-job execution
"""
import sys
import os

# Add the server path to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'server'))

import requests
import logging
import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

logging.basicConfig(
    level=logging.INFO,
    format="<RAG Sync Daemon> %(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("RAG Sync Daemon")


def sync_fix_experience_rag():
    """Call the Flask API to run the Fix Experience RAG sync"""
    try:
        logger.info("Starting Fix Experience RAG vector store sync")
        url = "http://localhost:80/rag/sync-fix-experience"
        
        response = requests.post(url, timeout=300)  # 5-minute timeout
        
        if response.status_code == 200:
            result = response.json()
            # ResponseManager response format: {'code': 200, 'data': {...}, 'message': ...}
            if result.get('code') == 200 and 'data' in result:
                data = result['data']
                message = data.get('message', '')
                stats = data.get('stats', {})
                logger.info(f"Fix Experience RAG sync completed successfully: {message}")
                logger.info(f"  - Success: {stats.get('success', 0)}")
                logger.info(f"  - Failure: {stats.get('failure', 0)}")
                logger.info(f"  - Total documents: {stats.get('total_documents', 0)}")
            else:
                error_msg = result.get('message', 'Unknown error')
                logger.error(f"Fix Experience RAG sync failed: {error_msg}")
                # Print the full response for debugging
                logger.error(f"Full response: {result}")
        else:
            logger.error(f"Fix Experience RAG sync request failed with status code: {response.status_code}")
            # Try to extract error details
            try:
                error_detail = response.json()
                logger.error(f"Error detail: {error_detail}")
            except:
                logger.error(f"Response text: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        logger.error("Fix Experience RAG sync request timeout (exceeded 5 minutes)")
    except Exception as e:
        logger.error(f"Failed to sync Fix Experience RAG vector store: {e}", exc_info=True)


def sync_code_library_rag():
    """Call the Flask API to run the Code Library RAG sync"""
    try:
        logger.info("Starting Code Library RAG vector store sync")
        url = "http://localhost:80/rag/sync-code-library"
        
        response = requests.post(url, timeout=300)  # 5-minute timeout
        
        if response.status_code == 200:
            result = response.json()
            # ResponseManager response format: {'code': 200, 'data': {...}, 'message': ...}
            if result.get('code') == 200 and 'data' in result:
                data = result['data']
                message = data.get('message', '')
                stats = data.get('stats', {})
                logger.info(f"Code Library RAG sync completed successfully: {message}")
                logger.info(f"  - Success: {stats.get('success', 0)}")
                logger.info(f"  - Failure: {stats.get('failure', 0)}")
                logger.info(f"  - Total documents: {stats.get('total_documents', 0)}")
            else:
                error_msg = result.get('message', 'Unknown error')
                logger.error(f"Code Library RAG sync failed: {error_msg}")
                # Print the full response for debugging
                logger.error(f"Full response: {result}")
        else:
            logger.error(f"Code Library RAG sync request failed with status code: {response.status_code}")
            # Try to extract error details
            try:
                error_detail = response.json()
                logger.error(f"Error detail: {error_detail}")
            except:
                logger.error(f"Response text: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        logger.error("Code Library RAG sync request timeout (exceeded 5 minutes)")
    except Exception as e:
        logger.error(f"Failed to sync Code Library RAG vector store: {e}", exc_info=True)


def sync_domain_knowledge_rag():
    """Call the Flask API to run the Domain Knowledge RAG sync"""
    try:
        logger.info("Starting Domain Knowledge RAG vector store sync")
        url = "http://localhost:80/rag/sync-domain-knowledge"
        
        response = requests.post(url, timeout=300)  # 5-minute timeout
        
        if response.status_code == 200:
            result = response.json()
            # ResponseManager response format: {'code': 200, 'data': {...}, 'message': ...}
            if result.get('code') == 200 and 'data' in result:
                data = result['data']
                message = data.get('message', '')
                stats = data.get('stats', {})
                logger.info(f"Domain Knowledge RAG sync completed successfully: {message}")
                logger.info(f"  - Success: {stats.get('success', 0)}")
                logger.info(f"  - Failure: {stats.get('failure', 0)}")
                logger.info(f"  - Total documents: {stats.get('total_documents', 0)}")
            else:
                error_msg = result.get('message', 'Unknown error')
                logger.error(f"Domain Knowledge RAG sync failed: {error_msg}")
                # Print the full response for debugging
                logger.error(f"Full response: {result}")
        else:
            logger.error(f"Domain Knowledge RAG sync request failed with status code: {response.status_code}")
            # Try to extract error details
            try:
                error_detail = response.json()
                logger.error(f"Error detail: {error_detail}")
            except:
                logger.error(f"Response text: {response.text[:500]}")
            
    except requests.exceptions.Timeout:
        logger.error("Domain Knowledge RAG sync request timeout (exceeded 5 minutes)")
    except Exception as e:
        logger.error(f"Failed to sync Domain Knowledge RAG vector store: {e}", exc_info=True)


def sync_rag_vector_store():
    """Sync all RAG vector stores"""
    logger.info("=" * 60)
    logger.info("Starting RAG vector stores sync (Fix Experience + Code Library + Domain Knowledge)")
    logger.info("=" * 60)
    
    # Sync Fix Experience
    sync_fix_experience_rag()
    
    # Sync Code Library
    sync_code_library_rag()
    
    # Sync Domain Knowledge
    sync_domain_knowledge_rag()
    
    logger.info("=" * 60)
    logger.info("All RAG vector stores sync completed")
    logger.info("=" * 60)


def get_fix_experience_sync_status():
    """Get the Fix Experience RAG sync status"""
    try:
        url = "http://localhost:80/rag/fix-experience-sync-status"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                status = result.get('data', {})
                logger.info(f"Fix Experience RAG sync status: {status}")
                return status
        return None
    except Exception as e:
        logger.error(f"Failed to get Fix Experience sync status: {e}")
        return None


def get_code_library_sync_status():
    """Get the Code Library RAG sync status"""
    try:
        url = "http://localhost:80/rag/code-library-sync-status"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                status = result.get('data', {})
                logger.info(f"Code Library RAG sync status: {status}")
                return status
        return None
    except Exception as e:
        logger.error(f"Failed to get Code Library sync status: {e}")
        return None


def get_domain_knowledge_sync_status():
    """Get the Domain Knowledge RAG sync status"""
    try:
        url = "http://localhost:80/rag/domain-knowledge-sync-status"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                status = result.get('data', {})
                logger.info(f"Domain Knowledge RAG sync status: {status}")
                return status
        return None
    except Exception as e:
        logger.error(f"Failed to get Domain Knowledge sync status: {e}")
        return None


def get_sync_status():
    """Get the sync status of all RAG stores"""
    logger.info("Fetching all RAG sync statuses...")
    fix_exp_status = get_fix_experience_sync_status()
    code_lib_status = get_code_library_sync_status()
    domain_knowledge_status = get_domain_knowledge_sync_status()
    
    return {
        'fix_experience': fix_exp_status,
        'code_library': code_lib_status,
        'domain_knowledge': domain_knowledge_status
    }


def check_server_inited():
    """Check whether the Flask server has been initialized"""
    try:
        url = "http://localhost:80/health/check"
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def scheduled_sync_fix_experience():
    """Scheduled job: Fix Experience RAG sync"""
    try:
        logger.info("[Scheduled Task] Fix Experience RAG sync triggered")
        sync_fix_experience_rag()
    except Exception as e:
        logger.error(f"[Scheduled Task] Fix Experience RAG sync failed: {e}", exc_info=True)


def scheduled_sync_code_library():
    """Scheduled job: Code Library RAG sync"""
    try:
        logger.info("[Scheduled Task] Code Library RAG sync triggered")
        sync_code_library_rag()
    except Exception as e:
        logger.error(f"[Scheduled Task] Code Library RAG sync failed: {e}", exc_info=True)


def scheduled_sync_domain_knowledge():
    """Scheduled job: Domain Knowledge RAG sync"""
    try:
        logger.info("[Scheduled Task] Domain Knowledge RAG sync triggered")
        sync_domain_knowledge_rag()
    except Exception as e:
        logger.error(f"[Scheduled Task] Domain Knowledge RAG sync failed: {e}", exc_info=True)


def main():
    """Main entry point"""
    logger.info("RAG Sync Daemon starting...")
    
    # Wait for the Flask server to start
    logger.info("Waiting for Flask server to initialize...")
    time.sleep(30)  # Wait 30 seconds for the server to start
    
    retry_count = 0
    max_retries = 60  # Retry at most 60 times (5 minutes total)
    
    while not check_server_inited():
        logger.info(f"Waiting for server to be initialized (attempt {retry_count + 1}/{max_retries})")
        time.sleep(5)
        retry_count += 1
        
        if retry_count >= max_retries:
            logger.error("Server failed to initialize after 5 minutes. Exiting.")
            sys.exit(1)
    
    logger.info("Flask server initialized successfully")
    
    # Run one sync immediately on startup
    logger.info("Running initial RAG sync for Fix Experience, Code Library and Domain Knowledge...")
    sync_rag_vector_store()
    
    # Show sync status
    statuses = get_sync_status()
    if statuses:
        if statuses.get('fix_experience'):
            logger.info(f"Fix Experience - Last sync: {statuses['fix_experience'].get('last_sync_timestamp', 'N/A')}, "
                       f"Total docs: {statuses['fix_experience'].get('total_documents', 0)}")
        if statuses.get('code_library'):
            logger.info(f"Code Library - Last sync: {statuses['code_library'].get('last_sync_timestamp', 'N/A')}, "
                       f"Total docs: {statuses['code_library'].get('total_documents', 0)}")
        if statuses.get('domain_knowledge'):
            logger.info(f"Domain Knowledge - Last sync: {statuses['domain_knowledge'].get('last_sync_timestamp', 'N/A')}, "
                       f"Total docs: {statuses['domain_knowledge'].get('total_documents', 0)}")
    
    # Create the scheduler
    logger.info("=" * 60)
    logger.info("Initializing APScheduler for periodic RAG sync:")
    logger.info("  - Fix Experience: every 30 minutes")
    logger.info("  - Code Library: every 1 hour")
    logger.info("  - Domain Knowledge: every 1 hour")
    logger.info("=" * 60)
    
    scheduler = BlockingScheduler(
        timezone=os.environ.get('SCHEDULER_TIMEZONE', 'UTC'),
        job_defaults={
            'coalesce': True,  # Merge missed runs
            'max_instances': 1,  # At most one running instance per job
            'misfire_grace_time': 300  # Grace period for a missed run (5 minutes)
        }
    )
    
    # Add the Fix Experience scheduled job (every 30 minutes)
    scheduler.add_job(
        func=scheduled_sync_fix_experience,
        trigger=IntervalTrigger(minutes=30),
        id='fix_experience_sync',
        name='Fix Experience RAG Sync',
        replace_existing=True
    )
    logger.info("✓ Added Fix Experience sync job (every 30 minutes)")
    
    # Add the Code Library scheduled job (every hour)
    scheduler.add_job(
        func=scheduled_sync_code_library,
        trigger=IntervalTrigger(hours=1),
        id='code_library_sync',
        name='Code Library RAG Sync',
        replace_existing=True
    )
    logger.info("✓ Added Code Library sync job (every 1 hour)")
    
    # Add the Domain Knowledge scheduled job (every hour)
    scheduler.add_job(
        func=scheduled_sync_domain_knowledge,
        trigger=IntervalTrigger(hours=1),
        id='domain_knowledge_sync',
        name='Domain Knowledge RAG Sync',
        replace_existing=True
    )
    logger.info("✓ Added Domain Knowledge sync job (every 1 hour)")
    
    # Start the scheduler (blocking)
    try:
        logger.info("=" * 60)
        logger.info("APScheduler started successfully")
        logger.info("RAG Sync Daemon is now running...")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("RAG Sync Daemon stopped by user")
        scheduler.shutdown(wait=False)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        scheduler.shutdown(wait=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
