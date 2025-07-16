#!/bin/bash

# AI Agent System Console Script
# Provides easy access to the CLI interface

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    print_error "Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source "$PROJECT_DIR/venv/bin/activate"

# Check if configuration exists
if [ ! -f "$PROJECT_DIR/config/.env" ]; then
    print_warning "Configuration file not found. Creating from template..."
    cp "$PROJECT_DIR/config/template.env" "$PROJECT_DIR/config/.env"
    print_warning "Please edit config/.env with your API keys and settings"
fi

# Change to project directory
cd "$PROJECT_DIR"

# Run the CLI with all arguments
print_status "Starting AI Agent System console..."
python -m console.cli "$@"