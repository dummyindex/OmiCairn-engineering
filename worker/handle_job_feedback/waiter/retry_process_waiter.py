# Import the shared-library path setup
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use the unified implementation from the shared library
from shared.waiter.retry_process_waiter import RetryProcessWaiter