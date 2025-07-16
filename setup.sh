#!/bin/bash

# setup.sh
# This script prepares a Debian 12 ARM device for running the AI Agent Configurator.
# It installs Node.js (via nvm), npm, and build tools.

echo "Starting setup for AI Agent Configurator on Debian 12 ARM..."

# 1. Update package lists
echo "Updating package lists..."
sudo apt update
if [ $? -ne 0 ]; then
    echo "Error: Failed to update package lists. Exiting."
    exit 1
fi

# 2. Install necessary tools: curl (for nvm), build-essential (for compiling native modules)
echo "Installing curl and build-essential..."
sudo apt install -y curl build-essential
if [ $? -ne 0 ]; then
    echo "Error: Failed to install curl or build-essential. Exiting."
    exit 1
fi

# 3. Install NVM (Node Version Manager)
echo "Installing NVM (Node Version Manager)..."
# Check if nvm is already installed
if [ -d "$HOME/.nvm" ]; then
    echo "NVM is already installed."
else
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
    if [ $? -ne 0 ]; then
        echo "Error: Failed to download or install NVM. Exiting."
        exit 1
    fi
    # Source nvm to make it available in the current shell
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion
    echo "NVM installed successfully."
fi

# Ensure nvm is sourced for the current session
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"

# 4. Install Node.js LTS version
echo "Installing Node.js LTS version..."
nvm install --lts
if [ $? -ne 0 ]; then
    echo "Error: Failed to install Node.js LTS. Exiting."
    exit 1
fi

# 5. Set the installed LTS version as default
echo "Setting Node.js LTS as default..."
nvm use --lts
nvm alias default lts/*
if [ $? -ne 0 ]; then
    echo "Error: Failed to set Node.js LTS as default. Exiting."
    exit 1
fi

echo "Node.js version: $(node -v)"
echo "npm version: $(npm -v)"

echo "Setup complete! You may need to close and reopen your terminal or run 'source ~/.bashrc' for nvm to be fully available."
echo "Now you can run './run.sh' to build and start the application."
