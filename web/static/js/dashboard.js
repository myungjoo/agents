// Dashboard JavaScript

// Global variables
let refreshInterval;
let currentAudits = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboard();
    setupEventListeners();
    startAutoRefresh();
});

// Setup event listeners
function setupEventListeners() {
    // Audit form submission
    document.getElementById('audit-form').addEventListener('submit', function(e) {
        e.preventDefault();
        startNewAudit();
    });
}

// Load dashboard data
async function loadDashboard() {
    try {
        await Promise.all([
            loadSystemStatus(),
            loadAudits(),
            loadAgents()
        ]);
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Error loading dashboard data', 'error');
    }
}

// Load system status
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        document.getElementById('active-audits').textContent = stats.active_audits || 0;
        document.getElementById('completed-audits').textContent = stats.completed_audits || 0;
        document.getElementById('total-issues').textContent = stats.total_issues || 0;
        document.getElementById('prs-created').textContent = stats.prs_created || 0;
    } catch (error) {
        console.error('Error loading system status:', error);
    }
}

// Load audits
async function loadAudits() {
    try {
        const response = await fetch('/api/audits');
        const audits = await response.json();
        currentAudits = audits;
        
        const tableBody = document.getElementById('audits-table');
        tableBody.innerHTML = '';
        
        if (audits.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No audits found</td></tr>';
            return;
        }
        
        audits.forEach(audit => {
            const row = createAuditRow(audit);
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading audits:', error);
    }
}

// Create audit table row
function createAuditRow(audit) {
    const row = document.createElement('tr');
    
    const startTime = new Date(audit.start_time);
    const duration = audit.end_time ? 
        formatDuration(new Date(audit.end_time) - startTime) : 
        formatDuration(Date.now() - startTime);
    
    row.innerHTML = `
        <td><code>${audit.audit_id.substring(0, 8)}</code></td>
        <td>${audit.repository_url}</td>
        <td>${audit.branch}</td>
        <td><span class="status-badge status-${audit.status}">${audit.status}</span></td>
        <td>${startTime.toLocaleString()}</td>
        <td>${duration}</td>
        <td>
            <button class="btn btn-sm btn-outline-primary" onclick="viewAuditDetails('${audit.audit_id}')">
                <i class="fas fa-eye"></i> View
            </button>
            ${audit.status === 'running' ? 
                `<button class="btn btn-sm btn-outline-danger" onclick="stopAudit('${audit.audit_id}')">
                    <i class="fas fa-stop"></i> Stop
                </button>` : ''
            }
        </td>
    `;
    
    return row;
}

// Load agents
async function loadAgents() {
    try {
        const response = await fetch('/api/agents');
        const agents = await response.json();
        
        const agentsGrid = document.getElementById('agents-grid');
        agentsGrid.innerHTML = '';
        
        agents.forEach(agent => {
            const card = createAgentCard(agent);
            agentsGrid.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading agents:', error);
    }
}

// Create agent card
function createAgentCard(agent) {
    const card = document.createElement('div');
    card.className = 'col-md-4 col-lg-3';
    
    const statusClass = getStatusClass(agent.status);
    const statusColor = getStatusColor(agent.status);
    
    card.innerHTML = `
        <div class="agent-card ${statusClass}">
            <div class="agent-header">
                <h6 class="agent-name">${agent.name}</h6>
                <span class="agent-status" style="background-color: ${statusColor}; color: white;">
                    ${agent.status}
                </span>
            </div>
            <div class="agent-metrics">
                <div class="metric">
                    <div class="metric-value">${agent.llm_calls || 0}</div>
                    <div class="metric-label">LLM Calls</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${(agent.total_llm_time || 0).toFixed(1)}s</div>
                    <div class="metric-label">LLM Time</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${(agent.memory_usage || 0).toFixed(1)}MB</div>
                    <div class="metric-label">Memory</div>
                </div>
            </div>
        </div>
    `;
    
    return card;
}

// Start new audit
async function startNewAudit() {
    const repositoryUrl = document.getElementById('repository-url').value;
    const branch = document.getElementById('branch').value;
    
    if (!repositoryUrl) {
        showNotification('Please enter a repository URL', 'warning');
        return;
    }
    
    const submitBtn = document.querySelector('#audit-form button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    
    try {
        submitBtn.innerHTML = '<span class="loading"></span> Starting...';
        submitBtn.disabled = true;
        
        const response = await fetch('/api/audit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repository: repositoryUrl,
                branch: branch
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification(`Audit started successfully! ID: ${result.audit_id}`, 'success');
            document.getElementById('audit-form').reset();
            loadDashboard();
        } else {
            showNotification(`Error starting audit: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error starting audit:', error);
        showNotification('Error starting audit', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// View audit details
async function viewAuditDetails(auditId) {
    try {
        const response = await fetch(`/api/audit/${auditId}`);
        const audit = await response.json();
        
        const modalContent = document.getElementById('audit-modal-content');
        modalContent.innerHTML = createAuditDetailsHTML(audit);
        
        const modal = new bootstrap.Modal(document.getElementById('auditModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading audit details:', error);
        showNotification('Error loading audit details', 'error');
    }
}

// Create audit details HTML
function createAuditDetailsHTML(audit) {
    let html = `
        <div class="audit-details">
            <div class="audit-section">
                <h6>Audit Information</h6>
                <p><strong>ID:</strong> ${audit.audit_id}</p>
                <p><strong>Repository:</strong> ${audit.repository_url}</p>
                <p><strong>Branch:</strong> ${audit.branch}</p>
                <p><strong>Status:</strong> <span class="status-badge status-${audit.status}">${audit.status}</span></p>
                <p><strong>Started:</strong> ${new Date(audit.start_time).toLocaleString()}</p>
                ${audit.end_time ? `<p><strong>Completed:</strong> ${new Date(audit.end_time).toLocaleString()}</p>` : ''}
            </div>
    `;
    
    // Add agent results
    if (audit.agent_results) {
        Object.entries(audit.agent_results).forEach(([agentName, result]) => {
            html += `
                <div class="audit-section">
                    <h6>${agentName.replace('_', ' ').toUpperCase()}</h6>
                    <p><strong>Status:</strong> <span class="status-badge status-${result.success ? 'completed' : 'failed'}">${result.success ? 'Success' : 'Failed'}</span></p>
                    ${result.error ? `<p><strong>Error:</strong> ${result.error}</p>` : ''}
                    ${result.data ? `<pre><code>${JSON.stringify(result.data, null, 2)}</code></pre>` : ''}
                </div>
            `;
        });
    }
    
    html += '</div>';
    return html;
}

// Stop audit
async function stopAudit(auditId) {
    if (!confirm('Are you sure you want to stop this audit?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/audit/${auditId}/stop`, {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('Audit stopped successfully', 'success');
            loadDashboard();
        } else {
            const result = await response.json();
            showNotification(`Error stopping audit: ${result.error}`, 'error');
        }
    } catch (error) {
        console.error('Error stopping audit:', error);
        showNotification('Error stopping audit', 'error');
    }
}

// Refresh audits
function refreshAudits() {
    loadDashboard();
}

// Start auto-refresh
function startAutoRefresh() {
    refreshInterval = setInterval(() => {
        loadSystemStatus();
        loadAudits();
        loadAgents();
    }, 10000); // Refresh every 10 seconds
}

// Stop auto-refresh
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
}

// Utility functions
function formatDuration(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes % 60}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
}

function getStatusClass(status) {
    const statusMap = {
        'running': 'info',
        'completed': 'success',
        'failed': 'danger',
        'stopped': 'warning',
        'idle': 'secondary'
    };
    return statusMap[status] || 'secondary';
}

function getStatusColor(status) {
    const colorMap = {
        'running': '#17a2b8',
        'completed': '#28a745',
        'failed': '#dc3545',
        'stopped': '#ffc107',
        'idle': '#6c757d'
    };
    return colorMap[status] || '#6c757d';
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});