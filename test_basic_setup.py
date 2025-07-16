#!/usr/bin/env python3
"""
Basic setup test for AI Agent System
Tests basic imports and structure without full installation
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that basic imports work"""
    try:
        # Test common imports
        from common.config.manager import ConfigManager
        from common.config.validator import ConfigValidator
        from common.utils.helpers import parse_size_string, sanitize_filename
        from common.llm.exceptions import LLMError, LLMTimeoutError
        
        # Test agent imports
        from agents.base_agent import BaseAgent, TaskResult, AgentStatus
        from agents.repo_analyzer.agent import RepoAnalyzerAgent
        from agents.issue_finder.agent import IssueFinderAgent
        from agents.code_tester.agent import CodeTesterAgent
        from agents.report_generator.agent import ReportGeneratorAgent
        
        print("✓ All imports successful")
        return True
        
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    try:
        # Test configuration validator
        from common.config.validator import ConfigValidator
        validator = ConfigValidator()
        schema = validator.get_schema()
        print(f"✓ Configuration validator works, schema has {len(schema)} sections")
        
        # Test utility functions
        from common.utils.helpers import parse_size_string, sanitize_filename
        size = parse_size_string("100MB")
        assert size == 100 * 1024 * 1024
        
        filename = sanitize_filename("file<>name.txt")
        assert "<" not in filename and ">" not in filename
        print("✓ Utility functions work")
        
        # Test agent capabilities
        from agents.repo_analyzer.agent import RepoAnalyzerAgent
        # Create a mock config and llm_manager for testing
        class MockConfig:
            def get(self, key, default=None):
                return default
        
        class MockLLMManager:
            pass
        
        agent = RepoAnalyzerAgent("test", MockConfig(), MockLLMManager())
        capabilities = agent.get_capabilities()
        print(f"✓ Repo analyzer agent has {len(capabilities)} capabilities")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def test_project_structure():
    """Test project structure"""
    required_dirs = [
        "common", "common/config", "common/llm", "common/utils",
        "agents", "agents/repo_analyzer", "agents/issue_finder", 
        "agents/code_tester", "agents/report_generator",
        "web", "web/templates", "console", "config"
    ]
    
    required_files = [
        "setup.py", "requirements.txt", "README.md",
        "config/config.example.yaml",
        "web/templates/dashboard.html"
    ]
    
    missing_dirs = []
    missing_files = []
    
    for directory in required_dirs:
        if not Path(directory).is_dir():
            missing_dirs.append(directory)
    
    for file_path in required_files:
        if not Path(file_path).is_file():
            missing_files.append(file_path)
    
    if missing_dirs:
        print(f"✗ Missing directories: {missing_dirs}")
        return False
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    
    print("✓ Project structure is complete")
    return True

def main():
    """Run all tests"""
    print("AI Agent System - Basic Setup Test")
    print("=" * 40)
    
    tests = [
        ("Project Structure", test_project_structure),
        ("Basic Imports", test_imports),
        ("Basic Functionality", test_basic_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"Test {test_name} failed")
        except Exception as e:
            print(f"Test {test_name} failed with exception: {e}")
    
    print(f"\n{'='*40}")
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Basic setup is working.")
        return 0
    else:
        print("✗ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())