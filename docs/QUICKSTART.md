# AI Agent System - Quick Start Guide

Get the AI Agent System up and running in minutes!

## Prerequisites

- Ubuntu 22.04/24.04 (or similar Linux distribution)
- Python 3.8+
- Git
- API keys for at least one LLM provider (OpenAI, Gemini, or Claude)

## Quick Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai-agent-system
```

### 2. Run Setup Script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

This script will:
- Install system dependencies
- Create Python virtual environment
- Install Python packages
- Set up system services
- Configure nginx and firewall
- Create necessary directories

### 3. Configure API Keys

```bash
nano config/.env
```

Edit the following variables with your API keys:

```env
# Choose your primary LLM provider
PRIMARY_LLM_PROVIDER=openai

# OpenAI (if using OpenAI)
OPENAI_API_KEY=your-openai-api-key

# Google Gemini (if using Gemini)
GEMINI_API_KEY=your-gemini-api-key

# Anthropic Claude (if using Claude)
CLAUDE_API_KEY=your-claude-api-key

# GitHub (for PR creation)
GITHUB_TOKEN=your-github-token
GITHUB_USERNAME=your-github-username
```

### 4. Start the System

```bash
sudo systemctl start ai-agents
sudo systemctl enable ai-agents
```

### 5. Verify Installation

```bash
# Check service status
sudo systemctl status ai-agents

# Run health check
./scripts/health-check.sh

# Access web interface
curl http://localhost:8080/api/health
```

## Using the System

### Web Interface

Open your browser and navigate to:
```
http://your-server-ip:8080
```

The web interface provides:
- Dashboard with system status
- Start new audits
- Monitor running audits
- View agent status
- Access audit results

### Console Interface

Use the console interface for command-line access:

```bash
# Start a new audit
./scripts/console.sh audit https://github.com/user/repo main

# Check audit status
./scripts/console.sh audit-status <audit-id>

# List all audits
./scripts/console.sh audits

# Monitor system
./scripts/console.sh monitor

# View system stats
./scripts/console.sh stats
```

### API Access

The system provides a REST API:

```bash
# Start audit
curl -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{"repository": "https://github.com/user/repo", "branch": "main"}'

# Get audit status
curl http://localhost:8080/api/audit/<audit-id>

# Get system stats
curl http://localhost:8080/api/stats
```

## Example Workflow

### 1. Start an Audit

```bash
# Via web interface: Enter repository URL and click "Start Audit"
# Via console:
./scripts/console.sh audit https://github.com/example/project main

# Via API:
curl -X POST http://localhost:8080/api/audit \
  -H "Content-Type: application/json" \
  -d '{"repository": "https://github.com/example/project", "branch": "main"}'
```

### 2. Monitor Progress

```bash
# Check status
./scripts/console.sh audit-status <audit-id>

# Monitor in real-time
./scripts/console.sh monitor

# View web dashboard
# Open http://localhost:8080
```

### 3. View Results

```bash
# Export results
./scripts/console.sh export <audit-id> --output results.json

# View in web interface
# Navigate to audit details in dashboard
```

## Configuration Options

### LLM Provider Selection

You can switch between LLM providers:

```bash
# Test providers
./scripts/console.sh test-llm openai
./scripts/console.sh test-llm gemini
./scripts/console.sh test-llm claude

# Switch primary provider
./scripts/console.sh switch-llm openai
```

### System Configuration

Key configuration options in `config/.env`:

```env
# System
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
MAX_CONCURRENT_AGENTS=5          # Maximum concurrent agents
AGENT_TIMEOUT=3600               # Agent timeout in seconds

# Web Interface
WEB_HOST=0.0.0.0                # Web interface host
WEB_PORT=8080                   # Web interface port

# Analysis
ANALYSIS_TIMEOUT=1800           # Analysis timeout
MAX_REPO_SIZE_MB=1000          # Maximum repository size
```

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
sudo journalctl -u ai-agents -f

# Check configuration
./scripts/console.sh config

# Verify API keys
./scripts/console.sh test-llm <provider>
```

#### 2. Web Interface Not Accessible

```bash
# Check if service is running
sudo systemctl status ai-agents

# Check port
sudo netstat -tlnp | grep 8080

# Check firewall
sudo ufw status
```

#### 3. LLM Calls Failing

```bash
# Test LLM provider
./scripts/console.sh test-llm <provider>

# Check API keys in config
cat config/.env | grep API_KEY

# Check rate limits
./scripts/console.sh stats
```

### Getting Help

```bash
# View system logs
sudo journalctl -u ai-agents -f

# Run health check
./scripts/health-check.sh

# Monitor system
./scripts/console.sh monitor

# Check configuration
./scripts/console.sh config
```

## Next Steps

### Advanced Configuration

- [Development Guide](DEVELOPMENT.md) - For developers and contributors
- [Architecture Documentation](ARCHITECTURE.md) - System architecture details
- [API Documentation](http://localhost:8080/api/docs) - Complete API reference

### Production Deployment

For production deployment, consider:

1. **SSL/TLS**: Enable HTTPS
2. **Database**: Use PostgreSQL instead of SQLite
3. **Monitoring**: Set up monitoring and alerting
4. **Backups**: Configure automated backups
5. **Security**: Review security settings

### Customization

- Add custom agents
- Integrate additional LLM providers
- Customize analysis rules
- Extend web interface

## Support

- **Documentation**: Check the docs/ directory
- **Issues**: Create GitHub issue
- **Discussions**: Use GitHub Discussions
- **Email**: Contact maintainers

---

You're now ready to use the AI Agent System! Start with a simple repository audit and explore the features as you become familiar with the system.