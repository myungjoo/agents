Advanced AI Agent System for Code Auditing
This project provides a complete, multi-agent framework designed for complex tasks like automated software analysis and bug fixing. It features a central controller, swappable LLM backends, and both web and console interfaces for monitoring and control.

System Architecture
FastAPI Controller: A central server (controller.py) that manages agent processes and serves the API and web UI.

REST API: Provides endpoints for UIs to list, start, stop, and check the status of agents.

Swappable LLM Providers: A modular system in /common/llm_providers.py allows easy switching between OpenAI, Gemini, or other LLM services via a configuration file.

Web UI: A real-time dashboard to monitor and interact with the agents.

Console UI: A full-featured command-line interface (cli.py) for remote management over SSH.

Modular Agents: Each agent resides in its own directory under /agents, with common logic shared from /agents/common_logic.

Project Structure
.
├── agents
│   ├── code_auditor
│   │   ├── __init__.py
│   │   └── main.py         # Main logic for the code auditor agent
│   └── common_logic
│       ├── __init__.py
│       └── base_agent.py   # Base class for all agents
├── common
│   ├── __init__.py
│   ├── llm_providers.py  # Abstraction for OpenAI, Gemini, etc.
│   └── tools.py          # Shared tools (git, shell, etc.)
├── web
│   └── templates
│       └── index.html      # The frontend for the web UI
├── .env.example            # Example for environment variables
├── config.ini              # System-wide configuration
├── controller.py           # Main FastAPI server (Agent Controller)
├── cli.py                  # Command-Line Interface
├── README.md
├── requirements.txt
└── setup.sh                # Installation script

Setup and Installation (for Ubuntu 22.04/24.04)
1. Clone the Repository
git clone <your-repo-url>
cd <your-repo-name>

2. Run the Setup Script
This script will check for dependencies, create a Python virtual environment, and install the required packages.

chmod +x setup.sh
./setup.sh

This will create a venv directory. All subsequent commands should be run with the virtual environment activated.

source venv/bin/activate

3. Configure Environment Variables
Copy the example .env file and fill in your API keys.

cp .env.example .env
nano .env

Fill in the required keys:

OPENAI_API_KEY="sk-..."
GOOGLE_API_KEY="AIza..."
# You will also need a GitHub token with repo access for the PR functionality
GITHUB_TOKEN="ghp_..."

4. Configure the System
Edit config.ini to select your preferred LLM provider and set other parameters.

[LLM]
# provider can be: openai, gemini, or cursor
provider = openai

[Controller]
host = 0.0.0.0
port = 8000

How to Run the System
Start the Agent Controller:
This is the central server and must be running for the UIs and agents to function.

python controller.py

Use the Web Interface:
Open your web browser and navigate to http://<your-server-ip>:8000. You will see the agent dashboard.

Use the Console Interface (from any SSH session):
You can manage the agents from the command line.

# List all available agents
python cli.py list

# Start the code_auditor agent
python cli.py start code_auditor

# Check the status of an agent
python cli.py status code_auditor

# Initiate a code audit job
python cli.py run-audit --repo_url https://github.com/user/repo

# Stop an agent
python cli.py stop code_auditor

