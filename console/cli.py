"""
Command Line Interface for AI Agent System

Provides a comprehensive CLI for monitoring and controlling AI agents
remotely via SSH.
"""

import click
import asyncio
import json
import os
import sys
from typing import Dict, Any, List
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

from agents.manager import AgentManager
from common.utils import Config, Logger
from common.llm import LLMFactory


console = Console()


@click.group()
@click.option('--config', '-c', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def cli(config, verbose):
    """AI Agent System Command Line Interface."""
    if config:
        os.environ['CONFIG_FILE'] = config
    
    if verbose:
        os.environ['LOG_LEVEL'] = 'DEBUG'


@cli.command()
@click.argument('repository')
@click.option('--branch', '-b', default='main', help='Repository branch')
@click.option('--wait', '-w', is_flag=True, help='Wait for completion')
def audit(repository, branch, wait):
    """Start a code audit for a repository."""
    async def run_audit():
        try:
            # Initialize agent manager
            agent_manager = AgentManager()
            await agent_manager.initialize()
            
            # Start audit
            with console.status(f"Starting audit for {repository}:{branch}..."):
                audit_id = await agent_manager.start_audit(repository, branch)
            
            console.print(f"[green]Audit started with ID: {audit_id}[/green]")
            
            if wait:
                await wait_for_audit_completion(agent_manager, audit_id)
            else:
                console.print(f"Monitor progress with: ai-agents audit-status {audit_id}")
                
        except Exception as e:
            console.print(f"[red]Error starting audit: {e}[/red]")
            sys.exit(1)
    
    asyncio.run(run_audit())


@cli.command()
@click.argument('audit_id')
def audit_status(audit_id):
    """Get status of a specific audit."""
    async def get_status():
        try:
            agent_manager = AgentManager()
            status = agent_manager.get_audit_status(audit_id)
            
            if not status:
                console.print(f"[red]Audit {audit_id} not found[/red]")
                return
            
            display_audit_status(status)
            
        except Exception as e:
            console.print(f"[red]Error getting audit status: {e}[/red]")
    
    asyncio.run(get_status())


@cli.command()
def audits():
    """List all audits."""
    async def list_audits():
        try:
            agent_manager = AgentManager()
            audits = agent_manager.get_all_audit_statuses()
            
            if not audits:
                console.print("[yellow]No audits found[/yellow]")
                return
            
            table = Table(title="Audits")
            table.add_column("Audit ID", style="cyan")
            table.add_column("Repository", style="green")
            table.add_column("Branch", style="blue")
            table.add_column("Status", style="yellow")
            table.add_column("Start Time", style="magenta")
            table.add_column("Duration", style="white")
            
            for audit_id, audit in audits.items():
                start_time = datetime.fromisoformat(audit['start_time'])
                duration = ""
                if audit.get('end_time'):
                    end_time = datetime.fromisoformat(audit['end_time'])
                    duration = str(end_time - start_time).split('.')[0]
                
                status_color = {
                    'running': 'green',
                    'completed': 'blue',
                    'failed': 'red',
                    'stopped': 'yellow'
                }.get(audit['status'], 'white')
                
                table.add_row(
                    audit_id[:8],
                    audit['repository_url'],
                    audit['branch'],
                    f"[{status_color}]{audit['status']}[/{status_color}]",
                    start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    duration
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error listing audits: {e}[/red]")
    
    asyncio.run(list_audits())


@cli.command()
@click.argument('audit_id')
def stop_audit(audit_id):
    """Stop a running audit."""
    async def stop():
        try:
            agent_manager = AgentManager()
            await agent_manager.stop_audit(audit_id)
            console.print(f"[green]Audit {audit_id} stopped[/green]")
            
        except Exception as e:
            console.print(f"[red]Error stopping audit: {e}[/red]")
    
    asyncio.run(stop())


@cli.command()
def agents():
    """List all agents and their status."""
    async def list_agents():
        try:
            agent_manager = AgentManager()
            agents = agent_manager.get_all_agent_statuses()
            
            if not agents:
                console.print("[yellow]No agents found[/yellow]")
                return
            
            table = Table(title="Agents")
            table.add_column("Agent ID", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("Type", style="blue")
            table.add_column("Status", style="yellow")
            table.add_column("LLM Calls", style="magenta")
            table.add_column("Total LLM Time", style="white")
            
            for agent_id, agent in agents.items():
                status_color = {
                    'idle': 'blue',
                    'running': 'green',
                    'completed': 'cyan',
                    'failed': 'red',
                    'stopped': 'yellow'
                }.get(agent['status'], 'white')
                
                table.add_row(
                    agent_id[:8],
                    agent['name'],
                    agent['type'],
                    f"[{status_color}]{agent['status']}[/{status_color}]",
                    str(agent['llm_calls']),
                    f"{agent['total_llm_time']:.2f}s"
                )
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error listing agents: {e}[/red]")
    
    asyncio.run(list_agents())


@cli.command()
@click.argument('agent_id')
def agent_status(agent_id):
    """Get status of a specific agent."""
    async def get_status():
        try:
            agent_manager = AgentManager()
            status = agent_manager.get_agent_status(agent_id)
            
            if not status:
                console.print(f"[red]Agent {agent_id} not found[/red]")
                return
            
            display_agent_status(status)
            
        except Exception as e:
            console.print(f"[red]Error getting agent status: {e}[/red]")
    
    asyncio.run(get_status())


@cli.command()
@click.argument('agent_id')
def stop_agent(agent_id):
    """Stop a specific agent."""
    async def stop():
        try:
            agent_manager = AgentManager()
            agent = agent_manager.get_agent(agent_id)
            
            if not agent:
                console.print(f"[red]Agent {agent_id} not found[/red]")
                return
            
            agent.stop()
            console.print(f"[green]Agent {agent_id} stopped[/green]")
            
        except Exception as e:
            console.print(f"[red]Error stopping agent: {e}[/red]")
    
    asyncio.run(stop())


@cli.command()
def stats():
    """Show system statistics."""
    async def show_stats():
        try:
            agent_manager = AgentManager()
            stats = agent_manager.get_system_stats()
            
            # Create layout
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="footer", size=3)
            )
            
            layout["main"].split_row(
                Layout(name="agents"),
                Layout(name="audits"),
                Layout(name="llm")
            )
            
            # Header
            layout["header"].update(Panel(
                f"AI Agent System Statistics - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                style="bold blue"
            ))
            
            # Agents section
            agents_table = Table(title="Agents")
            agents_table.add_column("Metric", style="cyan")
            agents_table.add_column("Value", style="green")
            
            agents_table.add_row("Total Agents", str(stats['agents']['total']))
            agents_table.add_row("Running Agents", str(stats['agents']['running']))
            agents_table.add_row("Idle Agents", str(stats['agents']['idle']))
            
            layout["agents"].update(Panel(agents_table))
            
            # Audits section
            audits_table = Table(title="Audits")
            audits_table.add_column("Metric", style="cyan")
            audits_table.add_column("Value", style="green")
            
            audits_table.add_row("Total Audits", str(stats['audits']['total']))
            audits_table.add_row("Running Audits", str(stats['audits']['running']))
            audits_table.add_row("Completed Audits", str(stats['audits']['completed']))
            audits_table.add_row("Failed Audits", str(stats['audits']['failed']))
            
            layout["audits"].update(Panel(audits_table))
            
            # LLM Providers section
            llm_table = Table(title="LLM Providers")
            llm_table.add_column("Provider", style="cyan")
            llm_table.add_column("Status", style="green")
            llm_table.add_column("Primary", style="yellow")
            
            for provider, info in stats['llm_providers'].items():
                status = "✓" if info['available'] else "✗"
                primary = "✓" if info['is_primary'] else ""
                llm_table.add_row(provider, status, primary)
            
            layout["llm"].update(Panel(llm_table))
            
            # Footer
            limits_text = Text()
            limits_text.append(f"Max Concurrent Agents: {stats['limits']['max_concurrent_agents']}\n")
            limits_text.append(f"Agent Timeout: {stats['limits']['agent_timeout']}s")
            
            layout["footer"].update(Panel(limits_text, title="System Limits"))
            
            console.print(layout)
            
        except Exception as e:
            console.print(f"[red]Error getting statistics: {e}[/red]")
    
    asyncio.run(show_stats())


@cli.command()
def llm_providers():
    """List available LLM providers."""
    async def list_providers():
        try:
            providers = LLMFactory.get_available_providers()
            
            table = Table(title="LLM Providers")
            table.add_column("Provider", style="cyan")
            table.add_column("Available", style="green")
            table.add_column("Primary", style="yellow")
            table.add_column("Model", style="blue")
            table.add_column("Max Tokens", style="magenta")
            
            for provider, info in providers.items():
                available = "✓" if info['available'] else "✗"
                primary = "✓" if info['is_primary'] else ""
                model = info['usage_info'].get('model', 'N/A')
                max_tokens = str(info['usage_info'].get('max_tokens', 'N/A'))
                
                table.add_row(provider, available, primary, model, max_tokens)
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error listing LLM providers: {e}[/red]")
    
    asyncio.run(list_providers())


@cli.command()
@click.argument('provider')
def test_llm(provider):
    """Test an LLM provider."""
    async def test():
        try:
            with console.status(f"Testing {provider}..."):
                result = LLMFactory.test_provider(provider)
            
            if 'error' in result:
                console.print(f"[red]Test failed: {result['error']}[/red]")
            else:
                console.print(f"[green]Test successful![/green]")
                console.print(f"Response: {result['response']}")
                console.print(f"Response time: {result['response_time']:.2f}s")
                console.print(f"Model: {result['model']}")
                
        except Exception as e:
            console.print(f"[red]Error testing provider: {e}[/red]")
    
    asyncio.run(test())


@cli.command()
@click.argument('provider')
def switch_llm(provider):
    """Switch primary LLM provider."""
    async def switch():
        try:
            success = LLMFactory.switch_primary_provider(provider)
            
            if success:
                console.print(f"[green]Switched to {provider} as primary provider[/green]")
            else:
                console.print(f"[red]Failed to switch to {provider}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error switching provider: {e}[/red]")
    
    asyncio.run(switch())


@cli.command()
def config():
    """Show system configuration."""
    try:
        config = Config()
        validation = config.validate_config()
        
        # Show configuration
        console.print(Panel(
            f"System Name: {config.get('system.name')}\n"
            f"Log Level: {config.get('system.log_level')}\n"
            f"Data Directory: {config.get('system.data_dir')}\n"
            f"Primary LLM Provider: {config.get('llm.primary_provider')}",
            title="Configuration"
        ))
        
        # Show validation results
        if validation['valid']:
            console.print("[green]Configuration is valid[/green]")
        else:
            console.print("[red]Configuration has errors:[/red]")
            for error in validation['errors']:
                console.print(f"  [red]• {error}[/red]")
        
        if validation['warnings']:
            console.print("[yellow]Configuration warnings:[/yellow]")
            for warning in validation['warnings']:
                console.print(f"  [yellow]• {warning}[/yellow]")
                
    except Exception as e:
        console.print(f"[red]Error showing configuration: {e}[/red]")


@cli.command()
@click.argument('audit_id')
@click.option('--output', '-o', help='Output file path')
def export(audit_id, output):
    """Export audit results."""
    async def export_results():
        try:
            agent_manager = AgentManager()
            config = Config()
            
            if not output:
                output = f"audit_{audit_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with console.status(f"Exporting audit {audit_id}..."):
                success = agent_manager.export_audit_results(audit_id, output)
            
            if success:
                console.print(f"[green]Audit results exported to {output}[/green]")
            else:
                console.print(f"[red]Failed to export audit {audit_id}[/red]")
                
        except Exception as e:
            console.print(f"[red]Error exporting audit: {e}[/red]")
    
    asyncio.run(export_results())


@cli.command()
def monitor():
    """Start real-time monitoring."""
    async def monitor_system():
        try:
            agent_manager = AgentManager()
            
            with Live(auto_refresh=False) as live:
                while True:
                    # Get current stats
                    stats = agent_manager.get_system_stats()
                    audits = agent_manager.get_all_audit_statuses()
                    agents = agent_manager.get_all_agent_statuses()
                    
                    # Create monitoring display
                    layout = create_monitoring_layout(stats, audits, agents)
                    live.update(layout)
                    
                    await asyncio.sleep(2)
                    
        except KeyboardInterrupt:
            console.print("\n[yellow]Monitoring stopped[/yellow]")
        except Exception as e:
            console.print(f"[red]Error in monitoring: {e}[/red]")
    
    asyncio.run(monitor_system())


def display_audit_status(status: Dict[str, Any]):
    """Display audit status in a formatted way."""
    console.print(Panel(
        f"Audit ID: {status['audit_id']}\n"
        f"Repository: {status['repository_url']}\n"
        f"Branch: {status['branch']}\n"
        f"Status: {status['status']}\n"
        f"Start Time: {status['start_time']}\n"
        f"End Time: {status.get('end_time', 'N/A')}",
        title="Audit Status"
    ))
    
    if status['agent_results']:
        table = Table(title="Agent Results")
        table.add_column("Agent", style="cyan")
        table.add_column("Success", style="green")
        table.add_column("Execution Time", style="blue")
        table.add_column("Error", style="red")
        
        for agent_type, result in status['agent_results'].items():
            success = "✓" if result['success'] else "✗"
            error = result.get('error', '')
            table.add_row(agent_type, success, f"{result['execution_time']:.2f}s", error)
        
        console.print(table)


def display_agent_status(status: Dict[str, Any]):
    """Display agent status in a formatted way."""
    console.print(Panel(
        f"Agent ID: {status['agent_id']}\n"
        f"Name: {status['name']}\n"
        f"Type: {status['type']}\n"
        f"Status: {status['status']}\n"
        f"LLM Calls: {status['llm_calls']}\n"
        f"Total LLM Time: {status['total_llm_time']:.2f}s\n"
        f"Memory Usage: {status['memory_usage']:.2f}MB",
        title="Agent Status"
    ))


async def wait_for_audit_completion(agent_manager: AgentManager, audit_id: str):
    """Wait for audit completion with progress display."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Waiting for audit completion...", total=None)
        
        while True:
            status = agent_manager.get_audit_status(audit_id)
            
            if not status:
                progress.update(task, description="Audit not found")
                break
            
            if status['status'] in ['completed', 'failed', 'stopped']:
                progress.update(task, description=f"Audit {status['status']}")
                break
            
            progress.update(task, description=f"Audit running... ({status['status']})")
            await asyncio.sleep(5)


def create_monitoring_layout(stats: Dict[str, Any], audits: Dict[str, Any], agents: Dict[str, Any]) -> Layout:
    """Create a monitoring layout."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    layout["main"].split_row(
        Layout(name="stats"),
        Layout(name="audits"),
        Layout(name="agents")
    )
    
    # Header
    layout["header"].update(Panel(
        f"AI Agent System Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        style="bold blue"
    ))
    
    # Stats section
    stats_text = Text()
    stats_text.append(f"Agents: {stats['agents']['running']}/{stats['agents']['total']} running\n")
    stats_text.append(f"Audits: {stats['audits']['running']}/{stats['audits']['total']} running\n")
    stats_text.append(f"Completed: {stats['audits']['completed']}\n")
    stats_text.append(f"Failed: {stats['audits']['failed']}")
    
    layout["stats"].update(Panel(stats_text, title="System Stats"))
    
    # Audits section
    audits_text = Text()
    for audit_id, audit in list(audits.items())[:5]:  # Show first 5
        status_color = {
            'running': 'green',
            'completed': 'blue',
            'failed': 'red',
            'stopped': 'yellow'
        }.get(audit['status'], 'white')
        
        audits_text.append(f"{audit_id[:8]}: ", style="cyan")
        audits_text.append(f"{audit['status']}\n", style=status_color)
    
    layout["audits"].update(Panel(audits_text, title="Recent Audits"))
    
    # Agents section
    agents_text = Text()
    for agent_id, agent in list(agents.items())[:5]:  # Show first 5
        status_color = {
            'running': 'green',
            'completed': 'blue',
            'failed': 'red',
            'stopped': 'yellow',
            'idle': 'white'
        }.get(agent['status'], 'white')
        
        agents_text.append(f"{agent['name']}: ", style="cyan")
        agents_text.append(f"{agent['status']}\n", style=status_color)
    
    layout["agents"].update(Panel(agents_text, title="Active Agents"))
    
    # Footer
    footer_text = Text()
    footer_text.append("Press Ctrl+C to stop monitoring")
    
    layout["footer"].update(Panel(footer_text, title="Controls"))
    
    return layout


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()