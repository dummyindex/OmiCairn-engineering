"""
Test runner script for omicairn-worker server tests.
Run this script to execute all server-related tests.
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run all server tests with appropriate configuration."""
    
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    print("=" * 80)
    print("Running omicairn-worker Server Tests")
    print("=" * 80)
    print()
    
    # Test categories
    test_categories = {
        "Unit Tests - Controllers": [
            "test_server_health.py",
            "test_server_controller_task.py",
            "test_server_controller_computation.py",
        ],
        "Unit Tests - Services": [
            "test_server_service_task.py",
            "test_server_service_computation.py",
            "test_server_dynamic_generation.py",
            "test_server_visualizer.py",
        ],
        "Unit Tests - Infrastructure": [
            "test_server_wrapper_tools.py",
        ],
        "Integration Tests": [
            "test_server_integration.py",
        ],
    }
    
    overall_success = True
    results = {}
    
    for category, test_files in test_categories.items():
        print(f"\n{'=' * 80}")
        print(f"{category}")
        print(f"{'=' * 80}\n")
        
        for test_file in test_files:
            test_path = tests_dir / test_file
            
            if not test_path.exists():
                print(f"⚠️  {test_file}: SKIPPED (file not found)")
                results[test_file] = "SKIPPED"
                continue
            
            print(f"Running {test_file}...")
            
            # Run pytest for this test file
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(test_path),
                    "-v",
                    "--tb=short",
                    "--color=yes",
                ],
                cwd=str(project_root),
                capture_output=False,
            )
            
            if result.returncode == 0:
                print(f"✅ {test_file}: PASSED")
                results[test_file] = "PASSED"
            else:
                print(f"❌ {test_file}: FAILED")
                results[test_file] = "FAILED"
                overall_success = False
            
            print()
    
    # Print summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    for test_file, result_status in results.items():
        if result_status == "PASSED":
            print(f"✅ {test_file}")
        elif result_status == "FAILED":
            print(f"❌ {test_file}")
        else:
            print(f"⚠️  {test_file}")
    
    print("\n" + "=" * 80)
    
    if overall_success:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


def run_with_coverage():
    """Run tests with coverage report."""
    project_root = Path(__file__).parent.parent
    
    print("Running tests with coverage...")
    print()
    
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_server_*.py",
            "-v",
            "--cov=server",
            "--cov-report=html",
            "--cov-report=term",
        ],
        cwd=str(project_root),
    )
    
    if result.returncode == 0:
        print("\n✅ Coverage report generated in htmlcov/index.html")
    
    return result.returncode


def run_specific_category(category):
    """Run tests for a specific category."""
    project_root = Path(__file__).parent.parent
    
    patterns = {
        "controllers": "test_server_controller_*.py",
        "services": "test_server_service_*.py",
        "integration": "test_server_integration.py",
        "all": "test_server_*.py",
    }
    
    pattern = patterns.get(category, "test_server_*.py")
    
    print(f"Running {category} tests...")
    print()
    
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            f"tests/{pattern}",
            "-v",
        ],
        cwd=str(project_root),
    )
    
    return result.returncode


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run omicairn-worker server tests")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--category",
        choices=["controllers", "services", "integration", "all"],
        help="Run specific test category"
    )
    
    args = parser.parse_args()
    
    if args.coverage:
        exit_code = run_with_coverage()
    elif args.category:
        exit_code = run_specific_category(args.category)
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code)
