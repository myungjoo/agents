# AI Agent System for Code Auditing

A comprehensive AI-powered system for automated code auditing, analysis, and improvement suggestions on Linux ARM/aarch64 devices.

## Features

- **Multi-Agent Architecture**: Specialized agents for different audit tasks
- **LLM Integration**: Support for ChatGPT, Gemini, and other LLM APIs
- **Web Interface**: Real-time monitoring and control dashboard
- **Console Interface**: SSH-accessible command-line interface
- **MCP & A2A Communication**: Advanced agent communication protocols
- **Automated Issue Detection**: Find correctness, memory, and performance bugs
- **Pull Request Generation**: Automated fix proposals with testing

## System Requirements

- **OS**: Ubuntu 22.04/24.04 LTS or Debian 12
- **Architecture**: ARM/aarch64 (optimized) or x86_64
- **Python**: 3.9 or higher
- **Memory**: 4GB+ RAM recommended
- **Storage**: 10GB+ free space

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ai-code-audit-agents

# Switch to the new branch
git checkout new

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Set up configuration
cp config/config.example.yaml config/config.yaml
# Edit config/config.yaml with your API keys and settings
```

### Configuration

1. **API Keys**: Set up your LLM API keys in `config/config.yaml`
2. **Database**: Configure SQLite or PostgreSQL settings
3. **Security**: Set up authentication tokens for web interface

### Running the System

```bash
# Start the web interface (default port: 8080)
ai-audit-web --config config/config.yaml

# Start console interface
ai-audit --help

# Run specific agent
ai-audit-agent --agent repo_analyzer --config config/config.yaml
```

## Architecture

### Agents

- **Repository Analyzer**: Analyzes project structure and purpose
- **Issue Finder**: Detects bugs and performance issues
- **Code Tester**: Tests proposed fixes and improvements
- **Report Generator**: Creates comprehensive audit reports

### Interfaces

- **Web Interface**: `http://localhost:8080` - Real-time dashboard
- **Console Interface**: SSH-accessible CLI for remote management

### Communication

- **MCP (Model Context Protocol)**: For LLM integration
- **A2A (Agent-to-Agent)**: Inter-agent communication
- **WebSocket**: Real-time updates for web interface

## Usage Examples

### Audit a GitHub Repository

```bash
# Via console
ai-audit analyze --repo https://github.com/user/repo.git

# Via web interface
# Navigate to http://localhost:8080 and use the repository input form
```

### Monitor Agent Status

```bash
# List all agents
ai-audit agents list

# Check specific agent status
ai-audit agents status --agent repo_analyzer

# View logs
ai-audit logs --agent issue_finder --tail 100
```

## Development

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_agents.py

# Run with coverage
pytest --cov=. --cov-report=html tests/
```

### Code Quality

```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy .

# Sort imports
isort .
```

## Security

- All API communications are encrypted
- Web interface requires authentication
- Agent processes run in isolated environments
- Input validation for all external data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Documentation**: See `docs/` directory
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions