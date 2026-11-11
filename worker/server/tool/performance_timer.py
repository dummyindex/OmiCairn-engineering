import time
from contextlib import contextmanager
from log.logger_factory import LoggerFactory
import os

logger = LoggerFactory.get_logger("PerformanceTimer")
TIMING_ENABLED = os.getenv('PERFORMANCE_TIMING_ENABLED', 'true').lower() == 'true'


@contextmanager
def timer_stage(name: str, timings: dict):
    """Context manager to time a code block and store result in timings dict.

    Args:
        name: The name/identifier for this timing stage
        timings: Dictionary to store the timing result (in milliseconds)

    Usage:
        timings = {}
        with timer_stage("db_query", timings):
            # code to time
            pass
        # timings["db_query"] now contains duration in ms
    """
    if not TIMING_ENABLED:
        yield
        return
    start = time.perf_counter()
    try:
        yield
    finally:
        timings[name] = (time.perf_counter() - start) * 1000


def log_timings(operation: str, timings: dict):
    """Log all captured timings for an operation.

    Args:
        operation: Name of the overall operation
        timings: Dictionary of stage names to durations in ms
    """
    if not TIMING_ENABLED or not timings:
        return
    total = sum(timings.values())
    logger.info(f"[Timer] {operation} - Total: {total:.2f}ms")
    for stage, duration in timings.items():
        logger.info(f"[Timer]   {stage}: {duration:.2f}ms")