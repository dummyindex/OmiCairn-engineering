#!/usr/bin/env python3
"""
Comprehensive test runner for omicairn-worker.
Runs all test suites and generates coverage reports.
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        end_time = time.time()
        print(f"✅ SUCCESS ({end_time - start_time:.2f}s)")
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        print(f"❌ FAILED ({end_time - start_time:.2f}s)")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print(f"❌ Command not found: {command[0]}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run omicairn-worker test suite")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, help="Number of parallel processes")
    parser.add_argument("--module", "-m", help="Run specific test module")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--markers", help="Run tests with specific markers")
    parser.add_argument("--no-cov", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--xml-report", action="store_true", help="Generate XML test report")
    
    args = parser.parse_args()
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"🚀 Starting omicairn-worker test suite")
    print(f"📁 Working directory: {project_root}")
    print(f"🐍 Python version: {sys.version}")
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"✅ pytest version: {pytest.__version__}")
    except ImportError:
        print("❌ pytest not installed. Please install with: pip install pytest")
        return 1
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    if args.module:
        cmd.append(f"tests/{args.module}")
    else:
        cmd.append("tests/")
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add pattern matching
    if args.pattern:
        cmd.extend(["-k", args.pattern])
    
    # Add markers
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    # Add coverage if requested
    if args.coverage and not args.no_cov:
        cmd.extend([
            "--cov=handle_dynamic_generation",
            "--cov=handle_job_feedback", 
            "--cov=handle_visualizer",
            "--cov=server",
            "--cov-report=term-missing"
        ])
        
        if args.html_report:
            cmd.append("--cov-report=html")
            
    # Add XML report for CI/CD
    if args.xml_report:
        cmd.append("--junitxml=test-results.xml")
    
    # Show test collection information
    cmd.append("--tb=short")
    cmd.append("--strict-markers")
    
    # Run the tests
    success = run_command(cmd, "Running test suite")
    
    if success:
        print(f"\n🎉 All tests completed successfully!")
        
        if args.coverage and args.html_report:
            print(f"📊 HTML coverage report generated in: htmlcov/index.html")
            
        if args.xml_report:
            print(f"📄 XML test report generated: test-results.xml")
            
        return 0
    else:
        print(f"\n💥 Test execution failed!")
        return 1

def run_specific_test_suites():
    """Run specific test suites individually."""
    test_suites = [
        ("test_dynamic_generation_apis.py", "Dynamic Generation APIs"),
        ("test_job_feedback_apis.py", "Job Feedback APIs"),
        ("test_visualizer_apis.py", "Visualizer APIs"),
        ("test_chat_apis.py", "Chat APIs"),
        ("test_server_core.py", "Server Core"),
        ("test_integration_scenarios.py", "Integration Scenarios"),
        ("test_performance.py", "Performance Tests"),
        ("test_security.py", "Security Tests"),
        ("test_edge_cases.py", "Edge Cases"),
        ("test_configuration.py", "Configuration Tests")
    ]
    
    results = []
    
    for test_file, description in test_suites:
        cmd = ["python", "-m", "pytest", f"tests/{test_file}", "-v", "--tb=short"]
        success = run_command(cmd, f"{description} ({test_file})")
        results.append((description, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    failed = 0
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{description:<30} {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {len(results)} | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        print("🎉 All test suites passed!")
        return 0
    else:
        print("💥 Some test suites failed!")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--suites":
        # Run individual test suites
        exit_code = run_specific_test_suites()
    else:
        # Run main test execution
        exit_code = main()
    
    sys.exit(exit_code)