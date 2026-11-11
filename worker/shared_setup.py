"""
Shared-library path setup module.
Import this module in each process to make sure the shared library is accessible.
"""
import sys
import os

# Get the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))

# Make sure the shared directory is on the Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Verify the shared library is accessible
try:
    import shared
    print(f"[INFO] Shared library accessible from: {shared.__file__}")
except ImportError as e:
    print(f"[WARNING] Cannot import shared library: {e}")