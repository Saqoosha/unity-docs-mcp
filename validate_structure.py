#!/usr/bin/env python3
"""Simple structure validation script that doesn't require dependencies."""

import os
import sys


def validate_project_structure():
    """Validate the project structure is correct."""
    base_dir = os.path.dirname(__file__)
    
    required_files = [
        'src/unity_docs_mcp/__init__.py',
        'src/unity_docs_mcp/server.py',
        'src/unity_docs_mcp/scraper.py',
        'src/unity_docs_mcp/parser.py',
        'tests/__init__.py',
        'tests/test_server.py',
        'tests/test_scraper.py',
        'tests/test_parser.py',
        'tests/test_integration.py',
        'requirements.txt',
        'requirements-dev.txt',
        'pyproject.toml',
        'README.md',
        'run_tests.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    else:
        print("✅ All required files are present!")
    
    # Validate Python syntax in main modules
    python_files = [
        'src/unity_docs_mcp/__init__.py',
        'src/unity_docs_mcp/server.py',
        'src/unity_docs_mcp/scraper.py',
        'src/unity_docs_mcp/parser.py'
    ]
    
    syntax_errors = []
    for file_path in python_files:
        full_path = os.path.join(base_dir, file_path)
        try:
            with open(full_path, 'r') as f:
                compile(f.read(), full_path, 'exec')
        except SyntaxError as e:
            syntax_errors.append((file_path, str(e)))
    
    if syntax_errors:
        print("❌ Syntax errors found:")
        for file_path, error in syntax_errors:
            print(f"  - {file_path}: {error}")
        return False
    else:
        print("✅ All Python files have valid syntax!")
    
    # Check file sizes (basic sanity check)
    size_checks = [
        ('src/unity_docs_mcp/server.py', 1000),  # Should be substantial
        ('src/unity_docs_mcp/scraper.py', 1000),
        ('src/unity_docs_mcp/parser.py', 1000),
        ('README.md', 500)
    ]
    
    size_issues = []
    for file_path, min_size in size_checks:
        full_path = os.path.join(base_dir, file_path)
        file_size = os.path.getsize(full_path)
        if file_size < min_size:
            size_issues.append((file_path, file_size, min_size))
    
    if size_issues:
        print("⚠️  Small file warnings (might be incomplete):")
        for file_path, actual, expected in size_issues:
            print(f"  - {file_path}: {actual} bytes (expected >{expected})")
    else:
        print("✅ All files have reasonable sizes!")
    
    return len(missing_files) == 0 and len(syntax_errors) == 0


def main():
    """Main validation function."""
    print("Unity Docs MCP Server - Project Structure Validation")
    print("=" * 55)
    
    if validate_project_structure():
        print("\n🎉 Project structure validation passed!")
        print("\nNext steps:")
        print("1. Install dependencies: uv pip install -r requirements.txt")
        print("2. Run tests: python run_tests.py")
        print("3. Test with MCP Inspector: mcp-inspector src/unity_docs_mcp/server.py")
        return 0
    else:
        print("\n❌ Project structure validation failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())