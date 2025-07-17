#!/bin/bash

echo "--- AI Agent System Setup ---"

# Check for Python 3 and venv
if ! command -v python3 &> /dev/null
then
    echo "❌ Error: python3 is not installed. Please install it first."
    exit 1
fi

if ! python3 -m venv --help &> /dev/null
then
    echo "❌ Error: python3-venv is not installed. Please run 'sudo apt-get install python3-venv' first."
    exit 1
fi

echo "✅ Python dependencies checked."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "🐍 Virtual environment already exists."
fi

# Activate virtual environment and install packages
echo "📦 Activating venv and installing packages from requirements.txt..."
source venv/bin/activate
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to install pip packages."
    exit 1
fi

echo "✅ Packages installed."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔑 Creating .env file from .env.example..."
    cp .env.example .env
    echo "   Please edit the .env file with your API keys."
else
    echo "🔑 .env file already exists."
fi

# Create jobs directory
mkdir -p jobs

echo ""
echo "--- 🎉 Setup Complete! ---"
echo "Next Steps:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Edit your API keys in the '.env' file."
echo "3. Edit the provider in 'config.ini' if you want to use something other than OpenAI."
echo "4. Run the controller: python controller.py"
echo "5. In another terminal (with venv activated), use the CLI: python cli.py --help"
echo "6. Open your browser to the URL shown by the controller to see the Web UI."

