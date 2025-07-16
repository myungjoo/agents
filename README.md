# AI Agent System for Code Auditing

A comprehensive AI agent system designed for automated code auditing, analysis, and improvement of software repositories, specifically optimized for Linux C/C++ projects on Ubuntu ARM devices.

## Overview

This system consists of multiple specialized AI agents that work together to:
- Analyze software system structure and purpose
- Identify correctness, memory, and performance issues
- Generate and test code improvements
- Create comprehensive audit reports
- Submit pull requests with fixes

### Key Features

- **Multi-LLM Support**: OpenAI GPT-4, Google Gemini, Anthropic Claude, and custom providers
- **Modular Architecture**: Each agent operates independently with clear interfaces
- **Real-time Monitoring**: Web dashboard and console interface for remote SSH access
- **Production Ready**: Systemd services, nginx, supervisor, monitoring, and backups
- **Extensible**: Easy to add new agents and LLM providers
- **MCP & A2A Integration**: Support for Model Context Protocol and Agent-to-Agent communication

## Architecture

### Core Components

- **Agent Manager**: Central coordination and monitoring system
- **Repository Analyzer**: Analyzes repository structure and build systems
- **Issue Detector**: Identifies bugs and performance issues
- **Code Fixer**: Generates fixes for identified issues
- **Test Runner**: Validates fixes and measures improvements
- **Report Generator**: Creates comprehensive audit reports
- **PR Creator**: Submits pull requests with fixes

### Interfaces

- **Web Interface**: Modern web UI for monitoring and control
- **Console Interface**: CLI for remote SSH access and management

## Quick Start

1. **Install Dependencies**:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```

2. **Configure API Keys**:
   ```bash
   cp config/template.env config/.env
   # Edit config/.env with your API keys (OpenAI, Gemini, Claude, GitHub)
   ```

3. **Start the System**:
   ```bash
   sudo systemctl start ai-agents
   sudo systemctl enable ai-agents
   ```

4. **Access Interfaces**:
   - Web UI: http://localhost:8080
   - Console: `./scripts/console.sh`
   - API Docs: http://localhost:8080/api/docs

5. **Verify Installation**:
   ```bash
   ./scripts/health-check.sh
   ```

## Usage

### Running a Code Audit

```bash
# Via web interface
curl -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{"repository": "https://github.com/user/repo", "branch": "main"}'

# Via console
./scripts/console.sh audit https://github.com/user/repo main
```

### Monitoring Agents

```bash
# List all agents
./scripts/console.sh agents list

# Check agent status
./scripts/console.sh agents status

# View logs
./scripts/console.sh logs
```

## Configuration

The system supports multiple LLM providers with automatic fallback:
- **OpenAI GPT-4**: Primary choice for code analysis
- **Google Gemini**: Alternative with good performance
- **Anthropic Claude**: High-quality reasoning capabilities
- **Custom providers**: Plugin system for custom LLM APIs

### LLM Provider Management

```bash
# Test available providers
./scripts/console.sh llm-providers

# Test specific provider
./scripts/console.sh test-llm openai

# Switch primary provider
./scripts/console.sh switch-llm gemini
```

## Directory Structure

```
├── agents/           # Individual agent implementations
├── common/           # Shared utilities and libraries
├── config/           # Configuration files
├── scripts/          # Management scripts
├── web/              # Web interface
├── console/          # Console interface
├── tests/            # Test suites
└── docs/             # Documentation
```

## Development

- **[Quick Start Guide](docs/QUICKSTART.md)** - Get up and running in minutes
- **[Development Guide](docs/DEVELOPMENT.md)** - Comprehensive development guidelines
- **[API Documentation](http://localhost:8080/api/docs)** - Complete API reference

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed guidelines.

## System Requirements

- **OS**: Ubuntu 22.04/24.04 (optimized for ARM devices)
- **Python**: 3.8+
- **Memory**: 4GB+ RAM recommended
- **Storage**: 20GB+ disk space
- **Network**: Internet access for LLM APIs and Git repositories

## License

MIT License - see [LICENSE](LICENSE) for details.