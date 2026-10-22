"""
Pytest configuration for omicairn-claude-code tests.
This ensures correct module import paths.
"""
import sys
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent

# Remove previous_app from path if it exists to avoid import conflicts
previous_app_path = str(project_root / "previous_app")
while previous_app_path in sys.path:
    sys.path.remove(previous_app_path)

# Add close_out_app to the BEGINNING of path to ensure correct imports
close_out_app_path = str(project_root / "close_out_app")
if close_out_app_path in sys.path:
    sys.path.remove(close_out_app_path)
sys.path.insert(0, close_out_app_path)

# Add previous_app after close_out_app
sys.path.insert(1, previous_app_path)
