#!/usr/bin/env python3
"""
Command Line Interface for docs-mcp.

Provides a user-friendly interface for managing documentation extraction,
testing, and server operations.
"""

import argparse
import asyncio
import sys
import subprocess
from pathlib import Path
from typing import Optional, List

# Import configurations and utilities
from .config import get_settings

def run_script(script_name: str, framework: Optional[str] = None) -> int:
    """Run a script from the scripts directory."""
    scripts_dir = Path(__file__).parent.parent.parent / "scripts"
    script_path = scripts_dir / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return 1
    
    try:
        cmd = [sys.executable, str(script_path)]
        if framework:
            cmd.extend(["--framework", framework])
        
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Script failed with exit code {e.returncode}")
        return e.returncode
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return 1

def run_test(test_name: Optional[str] = None, test_type: str = "all") -> int:
    """Run tests."""
    tests_dir = Path(__file__).parent.parent.parent / "tests"
    
    if test_name:
        if test_type == "integration":
            test_path = tests_dir / "integration" / f"test_{test_name}_integration.py"
        elif test_type == "unit":
            test_path = tests_dir / "unit" / f"test_{test_name}.py"
        else:
            # Try to find the test file
            integration_path = tests_dir / "integration" / f"test_{test_name}_integration.py"
            unit_path = tests_dir / "unit" / f"test_{test_name}.py"
            
            if integration_path.exists():
                test_path = integration_path
            elif unit_path.exists():
                test_path = unit_path
            else:
                print(f"❌ Test not found: {test_name}")
                return 1
        
        if not test_path.exists():
            print(f"❌ Test file not found: {test_path}")
            return 1
        
        cmd = [sys.executable, str(test_path)]
    else:
        # Run all tests
        cmd = [sys.executable, "-m", "pytest", str(tests_dir), "-v"]
    
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def extract_command(args) -> int:
    """Handle extract command."""
    if args.framework == "all":
        frameworks = ["python", "fastapi", "react", "swiftui", "tailwind", "figma", "figma_plugin", "css"]
        print("🚀 Extracting documentation for all frameworks...")
        
        for framework in frameworks:
            print(f"\n📚 Extracting {framework} documentation...")
            script_map = {
                "figma": "extract_figma_json.py",
                "figma_plugin": "extract_figma_plugin.py", 
                "css": "extract_mdn_css.py"
            }
            
            script = script_map.get(framework, "ingest_documentation.py")
            result = run_script(script, framework if framework not in script_map else None)
            
            if result != 0:
                print(f"❌ Failed to extract {framework} documentation")
                return result
        
        print("\n🎉 All documentation extracted successfully!")
        return 0
    
    else:
        script_map = {
            "figma": "extract_figma_json.py",
            "figma_plugin": "extract_figma_plugin.py",
            "css": "extract_mdn_css.py"
        }
        
        script = script_map.get(args.framework, "ingest_documentation.py")
        framework_arg = None if args.framework in script_map else args.framework
        
        return run_script(script, framework_arg)

def analyze_command(args) -> int:
    """Handle analyze command."""
    if args.stats:
        return run_script("analyze_collection.py")
    else:
        print("📊 Available analysis options:")
        print("  --stats    Show collection statistics")
        return 0

def test_command(args) -> int:
    """Handle test command."""
    if args.framework:
        return run_test(args.framework, "integration")
    elif args.all:
        return run_test()
    else:
        print("🧪 Available test options:")
        print("  --framework FRAMEWORK    Test specific framework integration")
        print("  --all                   Run all tests")
        return 0

def server_command(args) -> int:
    """Handle server command."""
    if args.start:
        server_path = Path(__file__).parent / "server.py"
        try:
            cmd = [sys.executable, str(server_path)]
            subprocess.run(cmd, check=True)
            return 0
        except subprocess.CalledProcessError as e:
            return e.returncode
    elif args.config:
        settings = get_settings()
        print("📋 Current configuration:")
        print(f"  ChromaDB data directory: {settings.chroma_data_dir}")
        print(f"  Environment: {settings.environment}")
        print(f"  MCP Server Host: {settings.mcp_server_host}")
        print(f"  MCP Server Port: {settings.mcp_server_port}")
        return 0
    else:
        print("🖥️  Available server options:")
        print("  --start     Start the MCP server")
        print("  --config    Show current configuration")
        return 0

def dev_command(args) -> int:
    """Handle development command."""
    if args.setup:
        print("🔧 Setting up development environment...")
        try:
            # Install dependencies
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"], check=True)
            
            # Create necessary directories
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            (data_dir / "logs").mkdir(exist_ok=True)
            (data_dir / "chroma_data").mkdir(exist_ok=True)
            
            print("✅ Development environment setup complete!")
            return 0
        except subprocess.CalledProcessError as e:
            print(f"❌ Setup failed: {e}")
            return 1
    
    elif args.clean:
        print("🧹 Cleaning temporary files...")
        # Clean up temporary files, logs, etc.
        temp_patterns = ["*.pyc", "__pycache__", ".pytest_cache", "*.log"]
        for pattern in temp_patterns:
            try:
                import glob
                for file in glob.glob(pattern, recursive=True):
                    Path(file).unlink()
                    print(f"  Removed: {file}")
            except Exception:
                pass
        
        print("✅ Cleanup complete!")
        return 0
    
    else:
        print("🛠️  Available development options:")
        print("  --setup     Setup development environment")
        print("  --clean     Clean temporary files")
        return 0

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="docs-mcp: Intelligent documentation search MCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  docs-mcp extract --framework python     Extract Python documentation
  docs-mcp extract --all                  Extract all documentation
  docs-mcp analyze --stats                Show collection statistics  
  docs-mcp test --framework figma         Test Figma integration
  docs-mcp server --start                 Start MCP server
  docs-mcp dev --setup                    Setup development environment
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract documentation")
    extract_parser.add_argument(
        "--framework", 
        choices=["python", "fastapi", "react", "swiftui", "tailwind", "figma", "figma_plugin", "css", "all"],
        required=True,
        help="Framework to extract documentation for"
    )
    
    # Analyze command  
    analyze_parser = subparsers.add_parser("analyze", help="Analyze documentation collection")
    analyze_parser.add_argument("--stats", action="store_true", help="Show collection statistics")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("--framework", help="Test specific framework integration")
    test_parser.add_argument("--all", action="store_true", help="Run all tests")
    
    # Server command
    server_parser = subparsers.add_parser("server", help="Server operations")
    server_parser.add_argument("--start", action="store_true", help="Start the MCP server")
    server_parser.add_argument("--config", action="store_true", help="Show configuration")
    
    # Dev command
    dev_parser = subparsers.add_parser("dev", help="Development utilities")
    dev_parser.add_argument("--setup", action="store_true", help="Setup development environment")
    dev_parser.add_argument("--clean", action="store_true", help="Clean temporary files")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    # Route to appropriate command handler
    command_handlers = {
        "extract": extract_command,
        "analyze": analyze_command, 
        "test": test_command,
        "server": server_command,
        "dev": dev_command
    }
    
    handler = command_handlers.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())