#!/usr/bin/env python3
"""
AI Agent System Test Script

This script tests the core functionality of the AI agent system
after dependencies have been installed via the setup script.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all core modules can be imported."""
    print("Testing module imports...")
    
    try:
        from common.utils import Logger, Config, DatabaseManager
        print("✓ Common utilities imported")
        
        from common.llm import LLMManager, LLMProvider
        print("✓ LLM management imported")
        
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_logger():
    """Test logger functionality."""
    print("\nTesting logger...")
    
    try:
        from common.utils import Logger
        
        logger = Logger("test")
        logger.info("Logger test message")
        logger.debug("Debug message")
        logger.warning("Warning message")
        
        # Test context logger
        context_logger = logger.with_context(component="test", version="1.0")
        context_logger.info("Context logger test")
        
        print("✓ Logger functionality working")
        return True
    except Exception as e:
        print(f"✗ Logger error: {e}")
        return False

def test_config():
    """Test configuration management."""
    print("\nTesting configuration...")
    
    try:
        from common.utils import Config
        
        # Test environment loading
        config = Config.load_from_env()
        print(f"✓ Configuration loaded: {config.log_level}")
        
        # Test validation
        issues = config.validate_config()
        if issues:
            print(f"⚠ Configuration issues: {issues}")
        else:
            print("✓ Configuration valid")
        
        # Test directory creation
        config.ensure_directories()
        print("✓ Directories ensured")
        
        return True
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return False

async def test_llm_manager():
    """Test LLM manager."""
    print("\nTesting LLM manager...")
    
    try:
        from common.llm import LLMManager
        
        # Create manager
        manager = LLMManager()
        print("✓ LLM Manager created")
        
        # Test stats (without initialization)
        stats = manager.get_stats()
        print(f"✓ Stats retrieved: {len(stats)} providers")
        
        # Test provider models
        providers = manager.get_available_providers()
        print(f"✓ Available providers: {providers}")
        
        return True
    except Exception as e:
        print(f"✗ LLM Manager error: {e}")
        return False

async def test_database():
    """Test database functionality."""
    print("\nTesting database...")
    
    try:
        from common.utils import DatabaseManager
        
        # Create test database
        db = DatabaseManager("sqlite:///test.db")
        
        # Test initialization
        result = await db.initialize()
        print(f"✓ Database initialized: {result}")
        
        # Clean up
        await db.close()
        Path("test.db").unlink(missing_ok=True)
        
        return True
    except Exception as e:
        print(f"✗ Database error: {e}")
        return False

def test_helpers():
    """Test helper utilities."""
    print("\nTesting helper utilities...")
    
    try:
        from common.utils.helpers import (
            get_system_info, format_bytes, format_duration,
            detect_language, sanitize_filename
        )
        
        # Test system info
        info = get_system_info()
        print(f"✓ System info: {info['cpu_count']} CPUs")
        
        # Test formatters
        bytes_str = format_bytes(1024 * 1024)
        duration_str = format_duration(3661)
        print(f"✓ Formatters: {bytes_str}, {duration_str}")
        
        # Test language detection
        lang = detect_language("test.py")
        print(f"✓ Language detection: {lang}")
        
        # Test filename sanitization
        safe_name = sanitize_filename("test/file:name")
        print(f"✓ Filename sanitization: {safe_name}")
        
        return True
    except Exception as e:
        print(f"✗ Helpers error: {e}")
        return False

async def main():
    """Main test function."""
    print("AI Agent System Test")
    print("===================")
    
    tests = [
        ("Module Imports", test_imports),
        ("Logger", test_logger),
        ("Configuration", test_config),
        ("Helper Utilities", test_helpers),
        ("LLM Manager", test_llm_manager),
        ("Database", test_database),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
                
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1
    
    print(f"\n\nTest Summary:")
    print(f"=============")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! System is working correctly.")
        return 0
    else:
        print(f"\n❌ {failed} tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)