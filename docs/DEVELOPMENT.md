# AI Agent System - Development Guide

This document provides comprehensive development guidelines, architecture details, and contribution information for the AI Agent System.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Development Setup](#development-setup)
3. [Agent Development](#agent-development)
4. [LLM Provider Integration](#llm-provider-integration)
5. [Testing](#testing)
6. [Deployment](#deployment)
7. [Contributing](#contributing)
8. [Troubleshooting](#troubleshooting)

## Architecture Overview

### System Components

The AI Agent System consists of several key components:

#### Core Components
- **Agent Manager**: Central coordination system for all agents
- **Base Agent**: Abstract base class for all AI agents
- **LLM Factory**: Manages multiple LLM providers with fallback support
- **Configuration System**: Centralized configuration management
- **Logging System**: Structured logging with JSON output

#### Agent Types
1. **Repository Analyzer**: Analyzes repository structure and build systems
2. **Issue Detector**: Identifies bugs and performance issues
3. **Code Fixer**: Generates fixes for identified issues
4. **Test Runner**: Validates fixes and measures improvements
5. **Report Generator**: Creates comprehensive audit reports
6. **PR Creator**: Submits pull requests with fixes

#### Interfaces
- **Web Interface**: FastAPI-based web UI with real-time updates
- **Console Interface**: CLI for remote SSH access and management
- **REST API**: Programmatic access to system functionality

### Data Flow

```
Repository → Repository Analyzer → Issue Detector → Code Fixer → Test Runner → Report Generator → PR Creator
```

Each agent passes its results to the next agent in the pipeline, with the Agent Manager coordinating the flow.

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- Ubuntu 22.04/24.04 (for production deployment)
- API keys for LLM providers (OpenAI, Gemini, Claude)

### Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai-agent-system
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**:
   ```bash
   cp config/template.env config/.env
   # Edit config/.env with your API keys
   ```

5. **Run setup script** (for production-like environment):
   ```bash
   ./scripts/setup.sh
   ```

### Development Tools

- **Code Formatting**: `black`, `isort`
- **Linting**: `pylint`, `flake8`, `mypy`
- **Testing**: `pytest`, `pytest-asyncio`
- **Pre-commit hooks**: Configured for code quality

## Agent Development

### Creating a New Agent

1. **Create agent directory**:
   ```bash
   mkdir agents/your_agent_name
   touch agents/your_agent_name/__init__.py
   touch agents/your_agent_name/agent.py
   ```

2. **Implement the agent**:
   ```python
   from agents.base import BaseAgent, AgentType, AgentContext, AgentResult
   
   class YourAgent(BaseAgent):
       def __init__(self):
           super().__init__(AgentType.YOUR_AGENT, "Your Agent Name")
       
       def get_capabilities(self) -> Dict[str, Any]:
           return {
               "name": "Your Agent Name",
               "description": "Description of what your agent does",
               "capabilities": ["capability1", "capability2"],
               "outputs": ["output1", "output2"]
           }
       
       async def execute(self, context: AgentContext) -> AgentResult:
           try:
               # Your agent logic here
               result_data = {
                   "key": "value"
               }
               
               return AgentResult(
                   success=True,
                   data=result_data,
                   metadata={"additional": "info"}
               )
           except Exception as e:
               return AgentResult(
                   success=False,
                   error=str(e)
               )
   ```

3. **Register the agent**:
   - Add to `agents/__init__.py`
   - Register in `web/app.py` startup event
   - Add to agent manager pipeline

### Agent Best Practices

1. **Error Handling**: Always wrap main logic in try-catch blocks
2. **Logging**: Use structured logging with relevant context
3. **LLM Calls**: Use the base class `call_llm` method for consistency
4. **Performance**: Track execution time and resource usage
5. **Testing**: Write comprehensive tests for your agent

### Agent Lifecycle

1. **Initialization**: Agent is created and registered
2. **Execution**: Agent receives context and executes logic
3. **Result**: Agent returns structured result with metadata
4. **Cleanup**: Agent resources are cleaned up

## LLM Provider Integration

### Adding a New LLM Provider

1. **Create provider class**:
   ```python
   from common.llm.base import LLMProvider, LLMProviderType, LLMRequest, LLMResponse
   
   class YourLLMProvider(LLMProvider):
       def _get_provider_type(self) -> LLMProviderType:
           return LLMProviderType.CUSTOM
       
       def _get_default_model(self) -> str:
           return "your-model-name"
       
       async def _call_api(self, request: LLMRequest) -> LLMResponse:
           # Implement API call logic
           pass
       
       def _validate_config(self) -> bool:
           # Validate configuration
           return True
   ```

2. **Register in factory**:
   ```python
   # In common/llm/factory.py
   LLMFactory.register_provider("your_provider", YourLLMProvider)
   ```

3. **Add configuration**:
   ```env
   # In config/template.env
   YOUR_PROVIDER_API_KEY=your-api-key
   YOUR_PROVIDER_ENDPOINT=https://your-api.com
   ```

### LLM Provider Best Practices

1. **Rate Limiting**: Implement appropriate rate limiting
2. **Error Handling**: Handle API errors gracefully
3. **Retry Logic**: Implement exponential backoff for failures
4. **Token Management**: Track and limit token usage
5. **Caching**: Cache responses when appropriate

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v
```

### Writing Tests

```python
import pytest
from agents.your_agent import YourAgent
from agents.base import AgentContext

@pytest.mark.asyncio
async def test_your_agent():
    agent = YourAgent()
    context = AgentContext(
        audit_id="test-audit",
        repository_url="https://github.com/test/repo",
        branch="main",
        working_directory="/tmp/test"
    )
    
    result = await agent.execute(context)
    
    assert result.success
    assert "expected_key" in result.data
```

### Test Structure

```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── fixtures/       # Test fixtures
└── conftest.py     # Pytest configuration
```

## Deployment

### Production Deployment

1. **System Requirements**:
   - Ubuntu 22.04/24.04
   - 4GB+ RAM
   - 20GB+ disk space
   - Python 3.8+

2. **Deployment Steps**:
   ```bash
   # Run setup script
   ./scripts/setup.sh
   
   # Configure environment
   nano config/.env
   
   # Start system
   sudo systemctl start ai-agents
   
   # Check status
   sudo systemctl status ai-agents
   ```

3. **Monitoring**:
   ```bash
   # View logs
   sudo journalctl -u ai-agents -f
   
   # Check health
   ./scripts/health-check.sh
   
   # Monitor system
   ./scripts/monitor.sh
   ```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x scripts/*.sh

EXPOSE 8080
CMD ["python", "-m", "web.app"]
```

### Environment Variables

Key environment variables for production:

```env
# System
LOG_LEVEL=INFO
DATA_DIR=/var/lib/ai_agents
WEB_HOST=0.0.0.0
WEB_PORT=8080

# LLM Providers
PRIMARY_LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
GEMINI_API_KEY=your-key
CLAUDE_API_KEY=your-key

# GitHub
GITHUB_TOKEN=your-token
GITHUB_USERNAME=your-username

# Security
WEB_SECRET_KEY=your-secret-key
ENABLE_SSL=true
```

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/your-feature`
3. **Make changes**: Follow coding standards
4. **Write tests**: Ensure good test coverage
5. **Run tests**: `pytest`
6. **Format code**: `black . && isort .`
7. **Commit changes**: Use conventional commit format
8. **Push and create PR**: Provide clear description

### Code Standards

- **Python**: PEP 8, type hints, docstrings
- **JavaScript**: ESLint, Prettier
- **HTML/CSS**: Bootstrap 5, responsive design
- **Git**: Conventional commits, meaningful messages

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Guidelines

1. **Clear title**: Describe the change
2. **Detailed description**: Explain what and why
3. **Screenshots**: For UI changes
4. **Tests**: Include relevant tests
5. **Documentation**: Update docs if needed

## Troubleshooting

### Common Issues

#### 1. LLM Provider Errors

**Problem**: LLM calls failing
**Solution**: Check API keys and rate limits

```bash
# Test LLM provider
./scripts/console.sh test-llm openai
```

#### 2. Agent Failures

**Problem**: Agents failing to execute
**Solution**: Check logs and dependencies

```bash
# View agent logs
sudo journalctl -u ai-agents | grep "agent"
```

#### 3. Web Interface Issues

**Problem**: Web interface not accessible
**Solution**: Check service status and ports

```bash
# Check service status
sudo systemctl status ai-agents

# Check port usage
sudo netstat -tlnp | grep 8080
```

#### 4. Performance Issues

**Problem**: System running slowly
**Solution**: Monitor resources and optimize

```bash
# Monitor system resources
htop

# Check agent performance
./scripts/console.sh stats
```

### Debug Mode

Enable debug logging:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run with debug
python -m web.app --log-level debug
```

### Log Analysis

```bash
# View recent logs
tail -f /var/log/ai_agents/system.log

# Search for errors
grep "ERROR" /var/log/ai_agents/system.log

# Monitor real-time
./scripts/console.sh monitor
```

## Performance Optimization

### System Tuning

1. **Database Optimization**:
   - Use PostgreSQL for production
   - Configure connection pooling
   - Implement proper indexing

2. **LLM Provider Optimization**:
   - Implement caching
   - Use batch processing
   - Optimize prompt engineering

3. **Agent Optimization**:
   - Parallel execution where possible
   - Resource cleanup
   - Memory management

### Monitoring

```bash
# System monitoring
./scripts/monitor.sh

# Performance metrics
./scripts/console.sh stats

# Resource usage
htop
```

## Security Considerations

1. **API Key Management**:
   - Use environment variables
   - Rotate keys regularly
   - Limit permissions

2. **Network Security**:
   - Enable SSL/TLS
   - Configure firewall
   - Use VPN for remote access

3. **Data Protection**:
   - Encrypt sensitive data
   - Implement access controls
   - Regular backups

## Support

For issues and questions:

1. **Documentation**: Check this guide and README
2. **Issues**: Create GitHub issue with details
3. **Discussions**: Use GitHub Discussions
4. **Email**: Contact maintainers directly

---

This development guide should help you get started with contributing to the AI Agent System. For additional questions or clarifications, please refer to the project documentation or create an issue.