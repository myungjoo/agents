# AI Agent System Installation Guide

This guide covers the installation and setup of the AI Agent System for code auditing on Linux systems, particularly Ubuntu 22.04/24.04 ARM/aarch64 devices.

## System Requirements

### Operating System
- **Ubuntu 22.04 LTS** or **Ubuntu 24.04 LTS** (recommended)
- **Debian 12** (supported)
- **Architecture**: ARM/aarch64 (optimized) or x86_64

### Hardware Requirements
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 10GB+ free space
- **Network**: Internet connection for LLM API calls and repository cloning

### Software Prerequisites
- **Python**: 3.9 or higher
- **Git**: For repository cloning
- **pip**: Python package manager

## Step 1: System Preparation

### Ubuntu/Debian Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv python3-dev git curl wget

# Install additional development tools
sudo apt install -y build-essential libffi-dev libssl-dev

# For ARM/aarch64 systems, install additional dependencies
sudo apt install -y gcc-aarch64-linux-gnu
```

### Create User for AI Agent System (Recommended)
```bash
# Create dedicated user for the agent system
sudo useradd -m -s /bin/bash ai-audit
sudo usermod -aG sudo ai-audit

# Switch to the ai-audit user
sudo su - ai-audit
```

## Step 2: Installation

### Clone Repository
```bash
# Clone the repository
git clone <repository-url> ai-code-audit-agents
cd ai-code-audit-agents

# Switch to the new branch with the implementation
git checkout new
```

### Python Environment Setup
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the AI agent system
pip install -e .
```

### Verify Installation
```bash
# Run basic setup test
python3 test_basic_setup.py

# Check installed commands
ai-audit --help
ai-audit-web --help
ai-audit-agent --help
```

## Step 3: Configuration

### Create Configuration
```bash
# Copy example configuration
cp config/config.example.yaml config/config.yaml

# Edit configuration file
nano config/config.yaml
```

### Required Configuration Changes

#### 1. LLM API Keys
Edit `config/config.yaml` and add your API keys:

```yaml
llm:
  default_provider: "openai"  # or "gemini", "anthropic"
  
  openai:
    api_key: "sk-your-openai-api-key-here"
    model: "gpt-4-turbo-preview"
    
  gemini:
    api_key: "your-gemini-api-key-here"
    
  anthropic:
    api_key: "your-anthropic-api-key-here"
```

#### 2. System Paths
```yaml
system:
  data_dir: "/home/ai-audit/data"
  temp_dir: "/tmp/ai-audit"
  log_level: "INFO"
```

#### 3. Web Interface
```yaml
web:
  host: "0.0.0.0"  # Allow external connections
  port: 8080
  secret_key: "change-this-to-a-secure-random-string"
  auth_required: true  # Enable for production
```

### Create Required Directories
```bash
# Create data and log directories
mkdir -p ~/data ~/logs
mkdir -p /tmp/ai-audit

# Set permissions
chmod 755 ~/data ~/logs
```

## Step 4: Testing

### Test Configuration
```bash
# Activate virtual environment
source venv/bin/activate

# Test console interface
ai-audit status
ai-audit agents
ai-audit health

# Test configuration
ai-audit config-show
```

### Test Individual Agents
```bash
# Test repository analyzer
ai-audit-agent --agent repo_analyzer --config config/config.yaml &

# Check agent status
ps aux | grep ai-audit-agent
```

### Test Web Interface
```bash
# Start web server
ai-audit-web --config config/config.yaml &

# Check if server is running
curl http://localhost:8080/api/status

# Access dashboard (if running locally with GUI)
# Open browser to http://localhost:8080
```

## Step 5: Production Deployment

### Systemd Services

#### Create Agent Service
```bash
sudo tee /etc/systemd/system/ai-audit-repo-analyzer.service > /dev/null <<EOF
[Unit]
Description=AI Audit Repository Analyzer Agent
After=network.target

[Service]
Type=simple
User=ai-audit
Group=ai-audit
WorkingDirectory=/home/ai-audit/ai-code-audit-agents
Environment=PATH=/home/ai-audit/ai-code-audit-agents/venv/bin
ExecStart=/home/ai-audit/ai-code-audit-agents/venv/bin/ai-audit-agent --agent repo_analyzer --config config/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Create Web Service
```bash
sudo tee /etc/systemd/system/ai-audit-web.service > /dev/null <<EOF
[Unit]
Description=AI Audit Web Dashboard
After=network.target

[Service]
Type=simple
User=ai-audit
Group=ai-audit
WorkingDirectory=/home/ai-audit/ai-code-audit-agents
Environment=PATH=/home/ai-audit/ai-code-audit-agents/venv/bin
ExecStart=/home/ai-audit/ai-code-audit-agents/venv/bin/ai-audit-web --config config/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Enable and Start Services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable ai-audit-repo-analyzer
sudo systemctl enable ai-audit-web

# Start services
sudo systemctl start ai-audit-repo-analyzer
sudo systemctl start ai-audit-web

# Check status
sudo systemctl status ai-audit-repo-analyzer
sudo systemctl status ai-audit-web
```

### Firewall Configuration
```bash
# Allow web interface access
sudo ufw allow 8080/tcp

# For SSH access (if not already configured)
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

### Nginx Reverse Proxy (Optional)
```bash
# Install nginx
sudo apt install -y nginx

# Create configuration
sudo tee /etc/nginx/sites-available/ai-audit > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain
    
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /ws {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/ai-audit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 6: Usage

### Console Interface (SSH Access)
```bash
# Connect via SSH
ssh ai-audit@your-server-ip

# Use console interface
ai-audit status
ai-audit analyze https://github.com/user/repo.git
ai-audit logs
ai-audit health
```

### Web Interface
1. Open browser to `http://your-server-ip:8080`
2. Use the dashboard to:
   - Monitor agent status
   - Start/stop agents
   - Submit repository analysis tasks
   - View real-time logs and metrics

### API Usage
```bash
# Get system status
curl http://your-server-ip:8080/api/status

# Start repository analysis
curl -X POST http://your-server-ip:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"repository_url": "https://github.com/user/repo.git"}'

# Get agent status
curl http://your-server-ip:8080/api/agents
```

## Troubleshooting

### Common Issues

#### 1. Permission Errors
```bash
# Fix permissions
sudo chown -R ai-audit:ai-audit /home/ai-audit/ai-code-audit-agents
chmod +x venv/bin/*
```

#### 2. Python Module Not Found
```bash
# Reinstall in virtual environment
source venv/bin/activate
pip install -e .
```

#### 3. LLM API Errors
- Verify API keys in `config/config.yaml`
- Check internet connectivity
- Verify API quotas and rate limits

#### 4. Port Already in Use
```bash
# Check what's using the port
sudo netstat -tlnp | grep :8080

# Kill process if necessary
sudo kill -9 <pid>
```

### Log Files
```bash
# System logs
sudo journalctl -u ai-audit-web -f
sudo journalctl -u ai-audit-repo-analyzer -f

# Application logs
tail -f logs/ai-audit.log
```

### Health Checks
```bash
# System health
ai-audit health

# Service status
sudo systemctl status ai-audit-web
sudo systemctl status ai-audit-repo-analyzer

# Process status
ps aux | grep ai-audit
```

## Security Considerations

1. **API Keys**: Store securely, never commit to version control
2. **Authentication**: Enable web interface authentication in production
3. **Firewall**: Only open necessary ports
4. **Updates**: Regularly update system packages and dependencies
5. **Monitoring**: Set up log monitoring and alerting
6. **Backup**: Regular backup of configuration and data

## Performance Tuning

### For ARM/aarch64 Systems
```yaml
# In config/config.yaml
system:
  max_workers: 2  # Adjust based on CPU cores
  
agents:
  max_concurrent: 1  # Reduce for limited memory
  
performance:
  worker_memory_limit: "1GB"  # Adjust based on available RAM
```

### Memory Optimization
```bash
# Monitor memory usage
htop
free -h

# Adjust Python memory settings
export PYTHONOPTIMIZE=1
export PYTHONDONTWRITEBYTECODE=1
```

## Maintenance

### Regular Tasks
```bash
# Update system
sudo apt update && sudo apt upgrade

# Update Python packages
source venv/bin/activate
pip install --upgrade -r requirements.txt

# Clean temporary files
rm -rf /tmp/ai-audit/*
```

### Backup Configuration
```bash
# Backup configuration
cp config/config.yaml config/config.yaml.backup.$(date +%Y%m%d)

# Backup data
tar -czf ~/ai-audit-backup-$(date +%Y%m%d).tar.gz ~/data ~/logs config/
```

This completes the installation and setup of the AI Agent System. The system is now ready for code auditing tasks on your Linux ARM/aarch64 device.