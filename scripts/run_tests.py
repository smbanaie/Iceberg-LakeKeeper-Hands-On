#!/usr/bin/env python3
"""
Script to run unit tests for the banking reconciliation system.
"""

import unittest
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests():
    """Run all unit tests."""
    print("Running unit tests...")
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('src/test/python', pattern='test_*.py')
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())
