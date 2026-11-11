#!/usr/bin/env python3
"""
Unit test runner for omicairn-backend project.
This script runs all unit tests for the server-side code.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def install_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    req_files = ["requirements.txt"]
    
    for req_file in req_files:
        if Path(req_file).exists():
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'install', 
                    '-r', req_file
                ], check=True, capture_output=True)
                print(f"[OK] Installed dependencies from {req_file}")
            except subprocess.CalledProcessError as e:
                print(f"[WARN] Failed to install from {req_file}: {e}")
    
    return True

def run_unit_tests(verbose=True, with_coverage=True, test_pattern=None, markers=None):
    """Run the unit tests."""
    print("\n" + "="*70)
    print("RUNNING OMICAIRN-BACKEND UNIT TESTS")
    print("="*70)
    
    cmd = [sys.executable, '-m', 'pytest']
    
    # Add test paths - updated to use new test structure
    if test_pattern:
        if test_pattern.startswith('server/'):
            cmd.append(test_pattern)
        else:
            cmd.append(f"server/tests/{test_pattern}")
    else:
        cmd.append("server/tests")
    
    # Add verbosity
    if verbose:
        cmd.append('-v')
    else:
        cmd.append('-q')
    
    # Add markers filter
    if markers:
        cmd.extend(['-m', markers])
    
    # Add other options
    cmd.extend([
        '--tb=short',
        '--strict-markers',
        '--disable-warnings',
        '--color=yes'
    ])
    
    # Add coverage if requested
    if with_coverage:
        cmd.extend([
            '--cov=server',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-report=xml:coverage.xml'
        ])
    
    # Add JUnit XML output
    cmd.append('--junit-xml=test_results.xml')
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=False)
        print(f"\nTests completed with exit code: {result.returncode}")
        return result.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

def print_test_summary():
    """Print test summary and available test categories."""
    print("\n" + "="*70)
    print("TEST STRUCTURE SUMMARY")
    print("="*70)
    
    test_categories = [
        ("Model Layer", "server/tests/unit/models/", "Data model and entity tests"),
        ("Auth Layer", "server/tests/unit/auth/", "Authentication and authorization tests"),
        ("Service Layer", "server/tests/unit/services/", "Business logic and service tests"),
        ("DAO Layer", "server/tests/unit/daos/", "Database access object tests"),
        ("Controller Layer", "server/tests/unit/controllers/", "API endpoint tests"),
        ("Integration Tests", "server/tests/integration/", "End-to-end workflow tests"),
        ("Wrapper Layer", "server/test/wrapper/", "Decorator and wrapper tests"),
        ("Utility/Tool Layer", "server/test/tool/", "Helper and utility function tests"),
        ("LLM Interface", "server/test/llm/", "AI/LLM interface tests"),
        ("Database Layer", "server/test/db/", "Database configuration tests"),
        ("Integration Tests", "server/test/integration/", "Cross-component integration tests"),
        ("Exception Handling", "server/test/exception/", "Custom exception tests"),
        ("End-to-End Tests", "tests/", "Complete workflow integration tests"),
    ]
    
    for category, path, description in test_categories:
        test_path = Path(path)
        if test_path.exists():
            test_files = list(test_path.glob("Test*.py"))
            print(f"  {category:20} {len(test_files):2} files - {description}")
    
    print("\nAVAILABLE MARKERS:")
    markers = [
        "unit", "integration", "service", "dao", "controller", 
        "gpt", "auth", "computation", "data", "slow", "external"
    ]
    for i, marker in enumerate(markers):
        if i % 6 == 0:
            print("\n  ", end="")
        print(f"{marker:12}", end="")
    print()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Run omicairn-backend unit tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_unit_tests.py                    # Run all tests
  python run_unit_tests.py --no-coverage     # Run without coverage
  python run_unit_tests.py -m unit           # Run only unit tests
  python run_unit_tests.py -m "service or dao"  # Run service or DAO tests
  python run_unit_tests.py --pattern "Test*Service*"  # Run service tests
  python run_unit_tests.py --quiet           # Run quietly
  python run_unit_tests.py --summary         # Show test structure only
        """
    )
    
    parser.add_argument('--no-install', action='store_true',
                       help='Skip dependency installation')
    parser.add_argument('--no-coverage', action='store_true',
                       help='Skip coverage reporting')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Run tests in quiet mode')
    parser.add_argument('--pattern', '-p', type=str,
                       help='Run specific test pattern (e.g., "Test*Service*")')
    parser.add_argument('-m', '--markers', type=str,
                       help='Run tests with specific markers (e.g., "unit", "service")')
    parser.add_argument('--summary', action='store_true',
                       help='Show test structure summary only')
    
    args = parser.parse_args()
    
    print("OmiCairn-backend Unit Test Suite")
    print("=" * 50)
    
    if args.summary:
        print_test_summary()
        return 0
    
    # Install dependencies if requested
    if not args.no_install:
        if not install_dependencies():
            print("Failed to install dependencies. Use --no-install to skip.")
            return 1
    
    # Run tests
    success = run_unit_tests(
        verbose=not args.quiet,
        with_coverage=not args.no_coverage,
        test_pattern=args.pattern,
        markers=args.markers
    )
    
    print("\n" + "=" * 70)
    if success:
        print("[SUCCESS] All tests passed!")
        
        # Show coverage report location
        if not args.no_coverage:
            print("\nCoverage reports generated:")
            print("  - HTML: htmlcov/index.html")
            print("  - XML: coverage.xml")
            print("  - JUnit: test_results.xml")
        
        print_test_summary()
        return 0
    else:
        print("[FAIL] Some tests failed!")
        print("\nTroubleshooting:")
        print("  - Check test output above for specific failures")
        print("  - Run with --pattern to test specific components")
        print("  - Run with -m unit to test only unit tests")
        print("  - Check pytest.ini configuration")
        return 1

if __name__ == '__main__':
    sys.exit(main())