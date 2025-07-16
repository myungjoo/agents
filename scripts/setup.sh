#!/bin/bash

# AI Agent System Setup Script
# This script sets up the AI agent system on Ubuntu 22.04/24.04

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

print_status "Starting AI Agent System setup..."

# Update system packages
print_status "Updating system packages..."
sudo apt update

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    sqlite3 \
    postgresql-client \
    nginx \
    supervisor \
    htop \
    tree \
    jq \
    unzip

# Install Python packages for development
print_status "Installing Python development packages..."
sudo apt install -y \
    python3-pylint \
    python3-flake8 \
    python3-mypy \
    python3-black \
    python3-isort

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
print_status "Creating system directories..."
sudo mkdir -p /var/lib/ai_agents/{audits,results,logs,exports}
sudo mkdir -p /var/log/ai_agents
sudo mkdir -p /etc/ai_agents

# Set permissions
print_status "Setting directory permissions..."
sudo chown -R $USER:$USER /var/lib/ai_agents
sudo chown -R $USER:$USER /var/log/ai_agents
sudo chmod -R 755 /var/lib/ai_agents
sudo chmod -R 755 /var/log/ai_agents

# Create configuration file
print_status "Creating configuration file..."
if [ ! -f config/.env ]; then
    cp config/template.env config/.env
    print_warning "Configuration file created at config/.env"
    print_warning "Please edit config/.env with your API keys and settings"
else
    print_status "Configuration file already exists"
fi

# Create systemd service file
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/ai-agents.service > /dev/null <<EOF
[Unit]
Description=AI Agent System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python -m web.app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create supervisor configuration
print_status "Creating supervisor configuration..."
sudo tee /etc/supervisor/conf.d/ai-agents.conf > /dev/null <<EOF
[program:ai-agents]
command=$(pwd)/venv/bin/python -m web.app
directory=$(pwd)
user=$USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/ai_agents/supervisor.log
EOF

# Create nginx configuration
print_status "Creating nginx configuration..."
sudo tee /etc/nginx/sites-available/ai-agents > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $(pwd)/web/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/ai-agents /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Create logrotate configuration
print_status "Creating logrotate configuration..."
sudo tee /etc/logrotate.d/ai-agents > /dev/null <<EOF
/var/log/ai_agents/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        systemctl reload ai-agents > /dev/null 2>&1 || true
    endscript
}
EOF

# Create firewall rules
print_status "Configuring firewall..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
    print_success "Firewall configured"
else
    print_warning "ufw not found, skipping firewall configuration"
fi

# Create backup script
print_status "Creating backup script..."
tee scripts/backup.sh > /dev/null <<EOF
#!/bin/bash
# Backup script for AI Agent System

BACKUP_DIR="/var/backups/ai-agents"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# Backup data
tar -czf \$BACKUP_DIR/ai-agents-data-\$DATE.tar.gz -C /var/lib/ai_agents .

# Backup logs
tar -czf \$BACKUP_DIR/ai-agents-logs-\$DATE.tar.gz -C /var/log/ai_agents .

# Backup configuration
tar -czf \$BACKUP_DIR/ai-agents-config-\$DATE.tar.gz config/

# Keep only last 7 days of backups
find \$BACKUP_DIR -name "ai-agents-*.tar.gz" -mtime +7 -delete

echo "Backup completed: \$BACKUP_DIR"
EOF

chmod +x scripts/backup.sh

# Create monitoring script
print_status "Creating monitoring script..."
tee scripts/monitor.sh > /dev/null <<EOF
#!/bin/bash
# Monitoring script for AI Agent System

source venv/bin/activate
python -m console.cli monitor
EOF

chmod +x scripts/monitor.sh

# Create health check script
print_status "Creating health check script..."
tee scripts/health-check.sh > /dev/null <<EOF
#!/bin/bash
# Health check script for AI Agent System

source venv/bin/activate

# Check if web interface is responding
if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
    echo "Web interface: OK"
else
    echo "Web interface: FAILED"
    exit 1
fi

# Check if agents are available
AGENT_COUNT=\$(python -c "
from agents.manager import AgentManager
import asyncio
async def check():
    manager = AgentManager()
    await manager.initialize()
    return len(manager.agents)
print(asyncio.run(check()))
")

if [ "\$AGENT_COUNT" -gt 0 ]; then
    echo "Agents: OK (\$AGENT_COUNT available)"
else
    echo "Agents: FAILED (no agents available)"
    exit 1
fi

echo "Health check: PASSED"
EOF

chmod +x scripts/health-check.sh

# Reload systemd and supervisor
print_status "Reloading system services..."
sudo systemctl daemon-reload
sudo systemctl enable ai-agents
sudo supervisorctl reread
sudo supervisorctl update

# Test the installation
print_status "Testing installation..."
if ./scripts/health-check.sh; then
    print_success "Installation test passed"
else
    print_warning "Installation test failed, but setup completed"
fi

# Final instructions
print_success "AI Agent System setup completed!"
echo
echo "Next steps:"
echo "1. Edit config/.env with your API keys and settings"
echo "2. Start the system: sudo systemctl start ai-agents"
echo "3. Check status: sudo systemctl status ai-agents"
echo "4. Access web interface: http://localhost"
echo "5. Use console interface: ./scripts/monitor.sh"
echo
echo "Useful commands:"
echo "  Start audit: python -m console.cli audit <repository>"
echo "  Check status: python -m console.cli stats"
echo "  Monitor: python -m console.cli monitor"
echo "  Backup: ./scripts/backup.sh"
echo
print_warning "Don't forget to configure your API keys in config/.env!"