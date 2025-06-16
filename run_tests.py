#!/usr/bin/env python3
"""
Test runner script for WinDAQExplorer.

Provides convenient commands for running different types of tests.
"""

import sys
import subprocess
import argparse


def run_command(cmd, description):
    """Run a command and handle the result."""
    print(f"\n{description}")
    print("=" * len(description))
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, text=True, 
                              capture_output=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Command failed with return code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Run tests for WinDAQExplorer")
    parser.add_argument("--unit", action="store_true", 
                       help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", 
                       help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", 
                       help="Run tests with coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--file", 
                       help="Run specific test file")
    
    args = parser.parse_args()
    
    # Base command
    cmd_parts = ["python", "-m", "pytest"]
    
    if args.verbose:
        cmd_parts.append("-v")
    
    if args.coverage:
        cmd_parts.extend(["--cov=wdq_app", "--cov-report=html", "--cov-report=term"])
    
    if args.unit:
        cmd_parts.extend(["-m", "unit"])
    elif args.integration:
        cmd_parts.extend(["-m", "integration"])
    
    if args.file:
        cmd_parts.append(args.file)
    else:
        cmd_parts.append("wdq_app/tests/")
    
    # Run the tests
    cmd = " ".join(cmd_parts)
    success = run_command(cmd, "Running WinDAQExplorer Tests")
    
    if args.coverage and success:
        print("\nCoverage report generated in htmlcov/index.html")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()