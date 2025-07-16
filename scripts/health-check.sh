#!/bin/bash

# AI Agent System Health Check Script
# Validates all system components and dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    PASSED_CHECKS=$((PASSED_CHECKS + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    FAILED_CHECKS=$((FAILED_CHECKS + 1))
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNING_CHECKS=$((WARNING_CHECKS + 1))
}

# Test function wrapper
run_check() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if eval "$test_command" &> /dev/null; then
        log_pass "$test_name"
        return 0
    else
        log_fail "$test_name"
        return 1
    fi
}

# Test function with warning
run_check_warn() {
    local test_name="$1"
    local test_command="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    if eval "$test_command" &> /dev/null; then
        log_pass "$test_name"
        return 0
    else
        log_warn "$test_name"
        return 1
    fi
}

log_info "AI Agent System Health Check"
log_info "============================"

# System checks
log_info ""
log_info "System Checks:"
log_info "--------------"

run_check "Python 3.8+ installed" "python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'"
run_check "pip3 available" "command -v pip3"
run_check "git available" "command -v git"
run_check "curl available" "command -v curl"

# Directory structure checks
log_info ""
log_info "Directory Structure:"
log_info "-------------------"

run_check "Data directory exists" "test -d data"
run_check "Logs directory exists" "test -d logs"
run_check "Config directory exists" "test -d config"
run_check "Scripts directory exists" "test -d scripts"
run_check "Common directory exists" "test -d common"
run_check "Agents directory exists" "test -d agents"

# Virtual environment checks
log_info ""
log_info "Virtual Environment:"
log_info "-------------------"

run_check "Virtual environment exists" "test -d venv"
run_check "Virtual environment Python" "test -f venv/bin/python"
run_check "Virtual environment pip" "test -f venv/bin/pip"

# Activate virtual environment for Python checks
if [[ -f "venv/bin/activate" ]]; then
    source venv/bin/activate
    log_info "Virtual environment activated"
else
    log_fail "Cannot activate virtual environment"
fi

# Python package checks
log_info ""
log_info "Python Dependencies:"
log_info "-------------------"

# Core packages
run_check "FastAPI installed" "python -c 'import fastapi'"
run_check "Uvicorn installed" "python -c 'import uvicorn'"
run_check "Pydantic installed" "python -c 'import pydantic'"
run_check "SQLAlchemy installed" "python -c 'import sqlalchemy'"

# LLM providers
run_check_warn "OpenAI installed" "python -c 'import openai'"
run_check_warn "Google Generative AI installed" "python -c 'import google.generativeai'"
run_check_warn "Anthropic installed" "python -c 'import anthropic'"

# Web framework
run_check "Jinja2 installed" "python -c 'import jinja2'"
run_check "Aiofiles installed" "python -c 'import aiofiles'"

# System utilities
run_check "psutil installed" "python -c 'import psutil'"
run_check "YAML installed" "python -c 'import yaml'"
run_check "Click installed" "python -c 'import click'"
run_check "Rich installed" "python -c 'import rich'"

# Git analysis
run_check "GitPython installed" "python -c 'import git'"

# Configuration checks
log_info ""
log_info "Configuration:"
log_info "-------------"

run_check "Environment file exists" "test -f config/.env"

# Test configuration loading
if run_check "Configuration loading" "python -c 'import sys; sys.path.append(\".\"); from common.utils import Config; Config.load_from_env()'"
then
    # Check for API keys
    if [[ -f "config/.env" ]]; then
        if grep -q "OPENAI_API_KEY=sk-" config/.env 2>/dev/null; then
            log_pass "OpenAI API key configured"
        elif grep -q "OPENAI_API_KEY=" config/.env 2>/dev/null; then
            log_warn "OpenAI API key placeholder (needs real key)"
        else
            log_warn "OpenAI API key not found"
        fi
        
        if grep -q "GEMINI_API_KEY=" config/.env 2>/dev/null && ! grep -q "GEMINI_API_KEY=$" config/.env 2>/dev/null; then
            log_pass "Gemini API key configured"
        else
            log_warn "Gemini API key not configured"
        fi
        
        if grep -q "ANTHROPIC_API_KEY=" config/.env 2>/dev/null && ! grep -q "ANTHROPIC_API_KEY=$" config/.env 2>/dev/null; then
            log_pass "Anthropic API key configured"
        else
            log_warn "Anthropic API key not configured"
        fi
    fi
fi

# Module import checks
log_info ""
log_info "AI Agent System Modules:"
log_info "-----------------------"

run_check "Common utilities import" "python -c 'import sys; sys.path.append(\".\"); from common.utils import Logger, Config'"
run_check "Database manager import" "python -c 'import sys; sys.path.append(\".\"); from common.utils import DatabaseManager'"
run_check "LLM manager import" "python -c 'import sys; sys.path.append(\".\"); from common.llm import LLMManager'"

# Test core functionality
log_info ""
log_info "Core Functionality:"
log_info "------------------"

# Test logger
if run_check "Logger functionality" "python -c 'import sys; sys.path.append(\".\"); from common.utils import Logger; logger = Logger(\"test\"); logger.info(\"test message\")'"; then
    log_pass "Logger working"
fi

# Test configuration validation
if run_check "Configuration validation" "python -c 'import sys; sys.path.append(\".\"); from common.utils import Config; config = Config.load_from_env(); config.validate_config()'"; then
    log_pass "Configuration validation working"
fi

# Test LLM manager initialization (without API calls)
if run_check "LLM manager creation" "python -c 'import sys; sys.path.append(\".\"); from common.llm import LLMManager; manager = LLMManager()'"; then
    log_pass "LLM manager creation working"
fi

# System resource checks
log_info ""
log_info "System Resources:"
log_info "----------------"

# Check disk space
DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
if [[ $DISK_USAGE -lt 80 ]]; then
    log_pass "Disk space sufficient (${DISK_USAGE}% used)"
else
    log_warn "Disk space low (${DISK_USAGE}% used)"
fi

# Check memory
MEMORY_USAGE=$(python -c "import psutil; print(int(psutil.virtual_memory().percent))")
if [[ $MEMORY_USAGE -lt 80 ]]; then
    log_pass "Memory usage normal (${MEMORY_USAGE}% used)"
else
    log_warn "Memory usage high (${MEMORY_USAGE}% used)"
fi

# Check if running on ARM
ARCH=$(uname -m)
if [[ "$ARCH" == "aarch64" || "$ARCH" == "arm64" ]]; then
    log_info "ARM architecture detected ($ARCH)"
    
    # ARM-specific checks
    run_check "ARM SSL support" "python -c 'import ssl; ssl.create_default_context()'"
    run_check "ARM SQLite support" "python -c 'import sqlite3; sqlite3.connect(\":memory:\")'"
fi

# Optional service checks
log_info ""
log_info "Optional Services:"
log_info "-----------------"

# Check if systemd service exists
if systemctl list-unit-files | grep -q "ai-agents.service"; then
    log_pass "Systemd service configured"
    
    if systemctl is-enabled ai-agents.service &>/dev/null; then
        log_pass "Systemd service enabled"
    else
        log_warn "Systemd service not enabled"
    fi
    
    if systemctl is-active ai-agents.service &>/dev/null; then
        log_pass "Systemd service running"
    else
        log_warn "Systemd service not running"
    fi
else
    log_warn "Systemd service not configured"
fi

# Check for nginx
if command -v nginx &> /dev/null; then
    log_pass "Nginx available"
    
    if systemctl is-active nginx &>/dev/null; then
        log_pass "Nginx running"
    else
        log_warn "Nginx not running"
    fi
else
    log_warn "Nginx not installed"
fi

# Database checks
log_info ""
log_info "Database:"
log_info "---------"

# Test SQLite database creation
if run_check "SQLite database creation" "python -c 'import sys, sqlite3; sys.path.append(\".\"); conn = sqlite3.connect(\"data/test.db\"); conn.close()'"; then
    rm -f data/test.db
    log_pass "SQLite functionality working"
fi

# Test database manager
if run_check "Database manager initialization" "python -c 'import sys, asyncio; sys.path.append(\".\"); from common.utils import DatabaseManager; asyncio.run(DatabaseManager(\"sqlite:///data/test.db\").initialize())'"; then
    rm -f data/test.db
    log_pass "Database manager working"
fi

# File permissions checks
log_info ""
log_info "File Permissions:"
log_info "----------------"

run_check "Data directory writable" "test -w data"
run_check "Logs directory writable" "test -w logs"
run_check "Config directory writable" "test -w config"

# Startup script checks
log_info ""
log_info "Scripts:"
log_info "-------"

run_check "Setup script executable" "test -x scripts/setup.sh"
run_check "Health check script executable" "test -x scripts/health-check.sh"

if [[ -f "scripts/start_system.py" ]]; then
    run_check "Start system script exists" "test -f scripts/start_system.py"
    run_check "Start system script executable" "test -x scripts/start_system.py"
fi

# Network connectivity checks (optional)
log_info ""
log_info "Network Connectivity:"
log_info "--------------------"

if run_check_warn "Internet connectivity" "curl -s --connect-timeout 5 https://www.google.com > /dev/null"; then
    run_check_warn "GitHub connectivity" "curl -s --connect-timeout 5 https://api.github.com > /dev/null"
    run_check_warn "OpenAI API reachable" "curl -s --connect-timeout 5 https://api.openai.com > /dev/null"
fi

# Summary
log_info ""
log_info "Health Check Summary:"
log_info "===================="

echo "Total checks: $TOTAL_CHECKS"
echo "Passed: $PASSED_CHECKS"
echo "Failed: $FAILED_CHECKS"
echo "Warnings: $WARNING_CHECKS"

if [[ $FAILED_CHECKS -eq 0 ]]; then
    if [[ $WARNING_CHECKS -eq 0 ]]; then
        log_info ""
        log_pass "🎉 All checks passed! System is ready to use."
        log_info ""
        log_info "Next steps:"
        log_info "1. Configure your API keys in config/.env"
        log_info "2. Start the system: python scripts/start_system.py"
        log_info "3. Access web interface: http://localhost:8080"
        exit 0
    else
        log_info ""
        log_warn "⚠️  System is functional but has warnings."
        log_info "Review the warnings above and configure missing components."
        exit 0
    fi
else
    log_info ""
    log_fail "❌ System has critical issues that need to be resolved."
    log_info "Fix the failed checks above before using the system."
    exit 1
fi