#!/usr/bin/env python3
"""Test runner script for Unity Docs MCP Server."""

import sys
import os
import unittest
import coverage

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def run_tests_with_coverage():
    """Run tests with coverage reporting."""
    # Initialize coverage
    cov = coverage.Coverage(source=['src/unity_docs_mcp'])
    cov.start()
    
    try:
        # Discover and run tests
        loader = unittest.TestLoader()
        start_dir = os.path.join(os.path.dirname(__file__), 'tests')
        suite = loader.discover(start_dir, pattern='test_*.py')
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Stop coverage and report
        cov.stop()
        cov.save()
        
        # Print coverage report
        print("\n" + "="*60)
        print("COVERAGE REPORT")
        print("="*60)
        cov.report(show_missing=True)
        
        # Generate HTML coverage report
        try:
            cov.html_report(directory='htmlcov')
            print(f"\nHTML coverage report generated in 'htmlcov' directory")
        except Exception as e:
            print(f"Could not generate HTML report: {e}")
        
        # Return exit code based on test results
        return 0 if result.wasSuccessful() else 1
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1
    finally:
        cov.stop()


def run_tests_simple():
    """Run tests without coverage (fallback)."""
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    try:
        # Try to run with coverage first
        import coverage
        exit_code = run_tests_with_coverage()
    except ImportError:
        print("Coverage not available, running tests without coverage...")
        exit_code = run_tests_simple()
    
    sys.exit(exit_code)