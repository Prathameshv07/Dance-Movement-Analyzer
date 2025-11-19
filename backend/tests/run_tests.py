"""
Test Runner for DanceDynamics
Runs all tests and generates coverage report
"""

import sys
import pytest
from pathlib import Path

def run_tests():
    """Run all tests with coverage reporting"""
    
    # Get test directory
    test_dir = Path(__file__).parent / "tests"
    
    # Pytest arguments
    pytest_args = [
        str(test_dir),
        "-v",  # Verbose output
        "--tb=short",  # Shorter traceback format
        "--color=yes",  # Colored output
        f"--cov=app",  # Coverage for app directory
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html",  # Generate HTML coverage report
    ]
    
    print("=" * 70)
    print("Running DanceDynamics Tests")
    print("=" * 70)
    print()
    
    # Run tests
    exit_code = pytest.main(pytest_args)
    
    print()
    print("=" * 70)
    if exit_code == 0:
        print("✓ All tests passed!")
        print("Coverage report generated in: htmlcov/index.html")
    else:
        print("✗ Some tests failed")
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
