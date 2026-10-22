"""
Test runner script for omicairn-claude-code tests

Run with: python run_tests.py [options]

Options:
  --integration Run only integration tests
  --coverage    Generate coverage report
  --verbose     Verbose output
"""
import sys
import os
import subprocess
import argparse


def main():
    parser = argparse.ArgumentParser(description='Run omicairn-claude-code tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--failfast', '-f', action='store_true', help='Stop on first failure')
    
    args = parser.parse_args()
    
    # Build test command
    if args.coverage:
        cmd = ['pytest', '--cov=previous_app', '--cov=close_out_app', '--cov-report=html', '--cov-report=term']
    else:
        cmd = ['pytest']
    
    if args.verbose:
        cmd.append('-v')
    
    if args.failfast:
        cmd.append('-x')
    
    # Select test files
    if args.integration:
        cmd.append('test_integration.py')
    else:
        # Run all tests
        cmd.append('.')
    
    # Set environment for tests
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print(f"Running tests: {' '.join(cmd)}")
    print(f"PYTHONPATH: {env['PYTHONPATH']}")
    print("-" * 80)
    
    # Run tests
    try:
        result = subprocess.run(cmd, env=env, cwd=os.path.dirname(__file__))
        return result.returncode
    except FileNotFoundError:
        print("\nError: pytest not found. Please install test requirements:")
        print("  pip install -r tests/requirements-test.txt")
        return 1


if __name__ == '__main__':
    sys.exit(main())
