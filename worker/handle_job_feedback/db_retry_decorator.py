"""
Database deadlock retry decorator

Automatically handles MySQL deadlock errors (Error 1213) by retrying with exponential backoff and random jitter.
"""

import time
import random
import logging
from functools import wraps
from sqlalchemy.exc import OperationalError

# Try to import the local logger_factory; fall back to standard logging on failure
try:
    from logger_factory import LoggerFactory
    logger = LoggerFactory.get_logger("db_retry")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("db_retry")


def retry_on_deadlock(max_retries=3, base_delay=0.1, max_delay=2.0):
    """
    Decorator: automatically retry on deadlock errors (MySQL Error 1213)
    
    MySQL InnoDB automatically rolls back one of the transactions when it detects a deadlock.
    This decorator catches the deadlock error and retries; the retry usually succeeds (because the other transaction has completed).
    
    Parameters:
    - max_retries: maximum number of retries (default 3, i.e. 4 attempts in total)
    - base_delay: base delay (seconds, default 0.1)
    - max_delay: maximum delay (seconds, default 2.0)
    
    Example:
        @retry_on_deadlock(max_retries=3)
        def update_node(node_id, attrs):
            with SessionLocal() as session:
                session.query(Node).filter(Node.id == node_id).update(attrs)
                session.commit()
    
    Log output when a deadlock occurs:
        WARNING: Deadlock detected in update_node (attempt 1/4), retrying in 0.123s...
        WARNING: Deadlock detected in update_node (attempt 2/4), retrying in 0.256s...
        INFO: update_node succeeded after 2 retries
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            func_name = func.__name__
            
            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # If there were earlier retries, log the success
                    if attempt > 0:
                        logger.info(
                            f"✅ {func_name} succeeded after {attempt} retries"
                        )
                    
                    return result
                    
                except OperationalError as e:
                    # Check whether this is a deadlock error (MySQL error code 1213)
                    is_deadlock = False
                    
                    if hasattr(e, 'orig') and hasattr(e.orig, 'args') and len(e.orig.args) >= 1:
                        error_code = e.orig.args[0]
                        if error_code == 1213:  # MySQL Deadlock
                            is_deadlock = True
                            last_exception = e
                    
                    if is_deadlock:
                        if attempt < max_retries:
                            # Exponential backoff: 0.1s, 0.2s, 0.4s, ...
                            delay = min(base_delay * (2 ** attempt), max_delay)
                            # Random jitter: prevents multiple transactions from retrying simultaneously
                            jitter = random.uniform(0, delay * 0.1)
                            sleep_time = delay + jitter
                            
                            # Truncate arguments for logging (avoid overly long logs)
                            args_preview = ""
                            if args:
                                if len(args) > 0:
                                    args_preview = f"arg0={args[0]}"
                                if len(args) > 1 and hasattr(args[1], '__name__'):
                                    args_preview += f", arg1={args[1].__name__}"
                                elif len(args) > 1:
                                    args_preview += f", arg1={type(args[1]).__name__}"
                            
                            logger.warning(
                                f"🔄 Deadlock detected in {func_name} "
                                f"(attempt {attempt + 1}/{max_retries + 1}), "
                                f"retrying in {sleep_time:.3f}s... "
                                f"[{args_preview}]"
                            )
                            
                            time.sleep(sleep_time)
                            continue
                        else:
                            # Maximum number of retries reached
                            logger.error(
                                f"❌ Deadlock in {func_name} failed after "
                                f"{max_retries + 1} attempts. Giving up."
                            )
                            raise
                    else:
                        # Not a deadlock error (possibly another OperationalError); re-raise immediately
                        raise
                        
                except Exception as e:
                    # Other exceptions are not retried; re-raise immediately
                    raise
            
            # Should be unreachable in theory, kept for safety
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


# Convenience alias for common use
retry_db_deadlock = retry_on_deadlock  # more intuitive name
