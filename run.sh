#!/bin/bash

# run.sh
# This script builds the React application and starts the Node.js server.

echo "Starting AI Agent Configurator application..."

# Ensure nvm is sourced for the current session
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# Check if Node.js is available
if ! command -v node &> /dev/null
then
    echo "Node.js is not found. Please run ./setup.sh first and ensure nvm is sourced."
    exit 1
fi

echo "Node.js version: $(node -v)"
echo "npm version: $(npm -v)"

# 1. Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Node.js dependencies. Exiting."
    exit 1
fi

# 2. Build the React application
echo "Building React application for production..."
npm run build
if [ $? -ne 0 ]; then
    echo "Error: Failed to build React application. Exiting."
    exit 1
fi

# 3. Start the Node.js server
echo "Starting Node.js server..."
# Use 'exec' to replace the current shell process with the node process,
