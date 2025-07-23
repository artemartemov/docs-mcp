#!/usr/bin/env python3
"""
Wrapper script to run quick_search.py from any directory
"""

import os
import sys
import subprocess

def main():
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Path to the quick_search.py script
    search_script = os.path.join(script_dir, 'quick_search.py')
    
    # Path to the virtual environment python
    venv_python = os.path.join(script_dir, 'venv', 'bin', 'python')
    
    # Check if virtual environment exists
    if os.path.exists(venv_python):
        python_exec = venv_python
    else:
        python_exec = sys.executable
    
    # Run the search script
    try:
        subprocess.run([python_exec, search_script], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running search: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"Python interpreter not found: {python_exec}")
        sys.exit(1)

if __name__ == "__main__":
    main()