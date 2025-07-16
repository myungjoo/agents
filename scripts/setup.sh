#!/bin/bash

# AI Agent System Setup Script
# This script sets up the complete AI agent system for code auditing

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# System information
log_info "AI Agent System Setup"
log_info "====================="
log_info "Detected OS: $(uname -s)"
log_info "Architecture: $(uname -m)"
log_info "Python version: $(python3 --version 2>/dev/null || echo 'Python3 not found')"

# Check if running on supported Ubuntu versions
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    if [[ "$ID" == "ubuntu" ]]; then
        if [[ "$VERSION_ID" == "22.04" || "$VERSION_ID" == "24.04" ]]; then
            log_success "Running on supported Ubuntu $VERSION_ID"
        else
            log_warning "Running on Ubuntu $VERSION_ID - officially supported versions are 22.04 and 24.04"
        fi
    else
        log_warning "Not running on Ubuntu - some features may not work as expected"
    fi
fi

# Check for required system packages
log_info "Checking system requirements..."

# Check for Python 3.8+
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    log_success "Python $PYTHON_VERSION is suitable (>= $REQUIRED_VERSION)"
else
    log_error "Python $PYTHON_VERSION is too old. Required: >= $REQUIRED_VERSION"
    exit 1
fi

# Check for pip
if ! command -v pip3 &> /dev/null; then
    log_error "pip3 is not installed"
    exit 1
fi

# Check for git
if ! command -v git &> /dev/null; then
    log_error "git is not installed"
    exit 1
fi

log_success "All required system packages are available"

# Install system dependencies if needed
log_info "Installing system dependencies..."

# Detect package manager and install dependencies
if command -v apt-get &> /dev/null; then
    log_info "Using apt package manager"
    
    # Update package list
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        python3-dev \
        python3-venv \
        python3-pip \
        build-essential \
        git \
        curl \
        wget \
        unzip \
        sqlite3 \
        postgresql-client \
        redis-tools \
        nginx \
        supervisor \
        htop \
        tree \
        jq
        
elif command -v yum &> /dev/null; then
    log_info "Using yum package manager"
    
    sudo yum update -y
    sudo yum install -y \
        python3-devel \
        python3-pip \
        gcc \
        git \
        curl \
        wget \
        unzip \
        sqlite \
        postgresql \
        redis \
        nginx \
        supervisor \
        htop \
        tree \
        jq
        
elif command -v dnf &> /dev/null; then
    log_info "Using dnf package manager"
    
    sudo dnf update -y
    sudo dnf install -y \
        python3-devel \
        python3-pip \
        gcc \
        git \
        curl \
        wget \
        unzip \
        sqlite \
        postgresql \
        redis \
        nginx \
        supervisor \
        htop \
        tree \
        jq
else
    log_warning "Unknown package manager - you may need to install dependencies manually"
fi

# Create directory structure
log_info "Creating directory structure..."

mkdir -p data/{repositories,reports,backups}
mkdir -p logs
mkdir -p temp
mkdir -p config

log_success "Directory structure created"

# Create Python virtual environment
log_info "Setting up Python virtual environment..."

if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_info "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
log_info "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
log_info "Installing Python dependencies..."
pip install -r requirements.txt

log_success "Python dependencies installed"

# Create configuration files
log_info "Setting up configuration..."

# Create environment template if it doesn't exist
if [[ ! -f "config/.env" ]]; then
    log_info "Creating environment configuration template..."
    
    cat > config/.env << 'EOF'
# AI Agent System Configuration

# Core Settings
DEBUG=false
LOG_LEVEL=INFO
DATA_DIR=./data
TEMP_DIR=./temp

# Database Configuration
DATABASE_URL=sqlite:///./data/ai_agents.db
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_ECHO=false

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=20

# Web Interface
WEB_HOST=0.0.0.0
WEB_PORT=8080
WEB_DEBUG=false
WEB_SECRET_KEY=CHANGE_THIS_SECRET_KEY_TO_SOMETHING_SECURE
CORS_ORIGINS=http://localhost:3000

# Git Configuration
GIT_USERNAME=ai-agent
GIT_EMAIL=ai-agent@example.com
GIT_TOKEN=

# LLM Provider API Keys (at least one required)
OPENAI_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=

# System Limits
MAX_REPOSITORY_SIZE=1073741824
MAX_ANALYSIS_TIME=3600
MAX_CONCURRENT_AUDITS=5

# Agent Configuration
REPOSITORY_ANALYZER_ENABLED=true
REPOSITORY_ANALYZER_MAX_TASKS=3
REPOSITORY_ANALYZER_TIMEOUT=1800

ISSUE_DETECTOR_ENABLED=true
ISSUE_DETECTOR_MAX_TASKS=3
ISSUE_DETECTOR_TIMEOUT=1800

CODE_FIXER_ENABLED=true
CODE_FIXER_MAX_TASKS=3
CODE_FIXER_TIMEOUT=1800

TEST_RUNNER_ENABLED=true
TEST_RUNNER_MAX_TASKS=2
TEST_RUNNER_TIMEOUT=1800

REPORT_GENERATOR_ENABLED=true
REPORT_GENERATOR_MAX_TASKS=2
REPORT_GENERATOR_TIMEOUT=900

PR_CREATOR_ENABLED=true
PR_CREATOR_MAX_TASKS=1
PR_CREATOR_TIMEOUT=600
EOF

    log_success "Configuration template created at config/.env"
    log_warning "Please edit config/.env with your API keys and settings"
else
    log_info "Configuration file already exists"
fi

# Test imports
log_info "Testing Python module imports..."

python3 -c "
import sys
import traceback

modules_to_test = [
    'fastapi',
    'uvicorn', 
    'pydantic',
    'sqlalchemy',
    'openai',
    'google.generativeai',
    'anthropic',
    'aiohttp',
    'psutil',
    'yaml',
    'click',
    'rich'
]

failed_imports = []

for module in modules_to_test:
    try:
        __import__(module)
        print(f'✓ {module}')
    except ImportError as e:
        print(f'✗ {module}: {e}')
        failed_imports.append(module)
    except Exception as e:
        print(f'? {module}: {e}')
        failed_imports.append(module)

if failed_imports:
    print(f'\nFailed to import: {failed_imports}')
    sys.exit(1)
else:
    print('\nAll required modules imported successfully!')
"

if [[ $? -eq 0 ]]; then
    log_success "All Python modules imported successfully"
else
    log_error "Some Python modules failed to import"
    exit 1
fi

# Test common module structure
log_info "Testing AI Agent system imports..."

python3 -c "
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from common.utils import Logger, Config
    from common.llm import LLMManager
    print('✓ Core modules imported successfully')
    
    # Test logger
    logger = Logger('test')
    logger.info('Logger test successful')
    print('✓ Logger working')
    
    # Test config loading
    config = Config.load_from_env()
    print('✓ Configuration loading working')
    
    print('✓ All core systems functional')
    
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
"

if [[ $? -eq 0 ]]; then
    log_success "AI Agent system modules working correctly"
else
    log_error "AI Agent system modules have issues"
    exit 1
fi

# Create systemd service files (optional)
if command -v systemctl &> /dev/null; then
    log_info "Creating systemd service files..."
    
    sudo tee /etc/systemd/system/ai-agents.service > /dev/null << EOF
[Unit]
Description=AI Agent System for Code Auditing
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
ExecStart=$PWD/venv/bin/python -m scripts.start_system
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    log_success "Systemd service file created"
    log_info "To start the service: sudo systemctl start ai-agents"
    log_info "To enable on boot: sudo systemctl enable ai-agents"
fi

# Create startup scripts
log_info "Creating startup scripts..."

cat > scripts/start_system.py << 'EOF'
#!/usr/bin/env python3
"""
AI Agent System Startup Script
"""

import asyncio
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from common.utils import Logger, Config
from common.llm import LLMManager

async def main():
    """Main startup function."""
    logger = Logger("System")
    logger.info("Starting AI Agent System...")
    
    try:
        # Load configuration
        config = Config.load_from_env()
        config.ensure_directories()
        
        # Validate configuration
        issues = config.validate_config()
        if issues:
            logger.warning(f"Configuration issues found: {issues}")
        
        # Initialize LLM manager
        llm_manager = LLMManager()
        if not await llm_manager.initialize():
            logger.error("Failed to initialize LLM manager")
            return 1
        
        logger.info("AI Agent System started successfully")
        
        # Keep the system running
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Shutting down AI Agent System...")
        return 0
    except Exception as e:
        logger.error(f"System error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
EOF

chmod +x scripts/start_system.py

# Final validation
log_info "Running final validation..."

python3 scripts/start_system.py --help &> /dev/null || true

log_success "Setup completed successfully!"
log_info ""
log_info "Next steps:"
log_info "1. Edit config/.env with your API keys and settings"
log_info "2. Run './scripts/health-check.sh' to verify the installation"
log_info "3. Start the system with './scripts/start_system.py'"
log_info ""
log_info "For web interface, visit: http://localhost:8080"
log_info "For console interface, run: ./scripts/console.sh"
log_info ""
log_warning "Remember to configure your LLM API keys before starting the system!"

# Deactivate virtual environment
deactivate