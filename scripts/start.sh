#!/bin/bash

# AI Agent System Start Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Check if configuration exists
if [ ! -f "config/.env" ]; then
    print_warning "Configuration file not found. Creating from template..."
    cp config/template.env config/.env
    print_warning "Please edit config/.env with your API keys before starting the system."
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Check if required packages are installed
print_status "Checking dependencies..."
if ! python -c "import fastapi, uvicorn, openai, anthropic" 2>/dev/null; then
    print_error "Required packages not found. Please run setup.sh first."
    exit 1
fi

# Check configuration
print_status "Validating configuration..."
python -c "
from common.utils import Config
config = Config()
validation = config.validate_config()
if not validation['valid']:
    print('Configuration errors:')
    for error in validation['errors']:
        print(f'  - {error}')
    exit(1)
if validation['warnings']:
    print('Configuration warnings:')
    for warning in validation['warnings']:
        print(f'  - {warning}')
print('Configuration is valid')
"

# Create necessary directories
print_status "Creating data directories..."
mkdir -p /var/lib/ai_agents/{audits,results,logs,exports}
mkdir -p /var/log/ai_agents

# Start the web interface
print_status "Starting AI Agent System..."
print_status "Web interface will be available at: http://localhost:8080"
print_status "API documentation: http://localhost:8080/api/docs"
print_status "Press Ctrl+C to stop"

# Start the application
python -m web.app