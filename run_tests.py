#!/usr/bin/env python3
"""
Test Runner for RhymeRarity
Comprehensive test suite runner with coverage reporting
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_unit_tests(verbose: bool = False, coverage: bool = False):
    """Run unit tests"""
    print("🧪 Running Unit Tests...")
    
    cmd = ["python", "-m", "pytest", "tests/unit/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=rhyme_core", "--cov-report=html", "--cov-report=term"])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def run_integration_tests(verbose: bool = False):
    """Run integration tests"""
    print("🔗 Running Integration Tests...")
    
    cmd = ["python", "-m", "pytest", "tests/integration/"]
    
    if verbose:
        cmd.append("-v")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def run_benchmark_tests():
    """Run benchmark tests"""
    print("📊 Running Benchmark Tests...")
    
    cmd = ["python", "tests/benchmark.py"]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="RhymeRarity Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark tests only")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run all
    if not any([args.unit, args.integration, args.benchmark]):
        args.all = True
    
    success = True
    
    if args.unit or args.all:
        success &= run_unit_tests(args.verbose, args.coverage)
    
    if args.integration or args.all:
        success &= run_integration_tests(args.verbose)
    
    if args.benchmark or args.all:
        success &= run_benchmark_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()


