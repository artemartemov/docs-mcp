#!/usr/bin/env python3
"""
Tests module entry point.
Allows running tests as: python -m tests
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run all tests using pytest"""
    tests_dir = Path(__file__).parent
    
    # Basic command to run pytest
    cmd = [sys.executable, "-m", "pytest", str(tests_dir), "-v"]
    
    # Add any command line arguments passed to this script
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    
    try:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        return 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())