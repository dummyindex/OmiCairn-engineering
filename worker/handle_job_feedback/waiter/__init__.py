# Re-export classes from the shared library for backward compatibility
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.waiter.retry_process_waiter import RetryProcessWaiter
from shared.waiter.dynamic_generation_waiter import DynamicGenerationWaiter

# Keep the original import paths working
__all__ = ['RetryProcessWaiter', 'DynamicGenerationWaiter']