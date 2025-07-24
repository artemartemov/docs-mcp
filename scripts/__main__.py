#!/usr/bin/env python3
"""
Scripts module entry point.
Allows running scripts as: python -m scripts [script_name]
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Main entry point for scripts module"""
    if len(sys.argv) < 2:
        print("Usage: python -m scripts <script_name> [args...]")
        print("Available scripts:")
        scripts_dir = Path(__file__).parent
        for script in scripts_dir.glob("*.py"):
            if script.name != "__main__.py":
                print(f"  {script.stem}")
        return 1
    
    script_name = sys.argv[1]
    if not script_name.endswith(".py"):
        script_name += ".py"
    
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        print(f"Script not found: {script_name}")
        return 1
    
    # Run the script with remaining arguments
    cmd = [sys.executable, str(script_path)] + sys.argv[2:]
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        return 0
    except Exception as e:
        print(f"Error running script: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())