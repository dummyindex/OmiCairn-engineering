#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run unit tests for the omicairn-worker daemon and handle modules
Usage: python run_daemon_tests.py [options]
"""

import sys
import os
import subprocess
from pathlib import Path

# Windows console encoding setup
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Make sure we are in the correct directory
WORKER_DIR = Path(__file__).parent.parent
os.chdir(WORKER_DIR)

def run_command(cmd, description):
    """Run a command and display the result"""
    print(f"\n{'='*80}")
    print(f">> {description}")
    print(f"{'='*80}\n")
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=False,
        text=True
    )
    
    if result.returncode == 0:
        print(f"\n[OK] {description} - succeeded")
    else:
        print(f"\n[FAIL] {description} - failed")
    
    return result.returncode

def main():
    """Main function"""
    print("""
+==============================================================+
|         omicairn-worker unit test runner                     |
|                                                              |
|  Test scope:                                                 |
|  - daemon/queue_job.py                                      |
|  - daemon/scan_timeout_computations.py                      |
|  - handle_dynamic_generation/index.py                       |
|  - handle_job_feedback/index.py                             |
+==============================================================+
    """)
    
    # Check arguments
    if len(sys.argv) > 1:
        option = sys.argv[1]
    else:
        option = "daemon"  # By default run only daemon tests
    
    total_failures = 0
    
    if option == "daemon":
        # Run daemon tests
        cmd = "python -m pytest tests/test_daemon_queue_job.py tests/test_daemon_scan_timeout.py -v --tb=short"
        total_failures += run_command(cmd, "Daemon module tests")
        
    elif option == "handle":
        # Run handle tests
        cmd = "python -m pytest tests/test_handle_dynamic_generation.py tests/test_handle_job_feedback_core.py -v --tb=short"
        total_failures += run_command(cmd, "Handle module tests")
        
    elif option == "all":
        # Run all tests
        cmd = "python -m pytest tests/test_daemon_queue_job.py tests/test_daemon_scan_timeout.py tests/test_handle_dynamic_generation.py tests/test_handle_job_feedback_core.py -v --tb=short"
        total_failures += run_command(cmd, "All unit tests")
        
    elif option == "coverage":
        # Run tests and generate a coverage report
        cmd = "python -m pytest tests/test_daemon_*.py --cov=daemon --cov-report=term-missing --cov-report=html -v"
        total_failures += run_command(cmd, "Test coverage analysis")
        
        if total_failures == 0:
            print("\n[INFO] Coverage report generated at: htmlcov/index.html")
        
    elif option == "quick":
        # Quick tests (run only key tests)
        cmd = "python -m pytest tests/test_daemon_queue_job.py::TestGetImageName tests/test_daemon_scan_timeout.py::TestInit -v"
        total_failures += run_command(cmd, "Quick tests")
        
    elif option == "help" or option == "-h" or option == "--help":
        print("""
Usage:
    python run_daemon_tests.py [option]

Options:
    daemon      - Run only daemon tests (default)
    handle      - Run only handle tests
    all         - Run all tests
    coverage    - Run tests and generate a coverage report
    quick       - Quick tests (run only key tests)
    help        - Show this help message

Examples:
    python run_daemon_tests.py daemon
    python run_daemon_tests.py all
    python run_daemon_tests.py coverage
        """)
        return 0
        
    else:
        print(f"[ERROR] Unknown option: {option}")
        print("Use 'python run_daemon_tests.py help' to see help")
        return 1
    
    # Show summary
    print(f"\n{'='*80}")
    if total_failures == 0:
        print("[SUCCESS] All tests passed!")
    else:
        print(f"[FAILED] {total_failures} test(s) failed")
    print(f"{'='*80}\n")
    
    return total_failures

if __name__ == "__main__":
    sys.exit(main())
