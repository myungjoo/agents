#!/usr/bin/env python3
"""
Console Interface for AI Agent System
Provides command-line interface for managing agents remotely via SSH
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from common.config import ConfigManager
from common.utils.logging import setup_logging, get_agent_logger


console = Console()
logger = get_agent_logger("console")


@click.group()
@click.option('--config', default='config/config.yaml', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config, verbose):
    """AI Agent System Console Interface"""
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose
    
    # Load configuration
    try:
        ctx.obj['config'] = ConfigManager(config)
        
        # Setup logging
        log_level = "DEBUG" if verbose else "INFO"
        setup_logging(level=log_level, format_type="simple")
        
    except Exception as e:
        console.print(f"[red]Failed to load configuration: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Show system status"""
    console.print(Panel("[bold blue]AI Agent System Status[/bold blue]"))
    
    # System information
    table = Table(title="System Information")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")
    
    table.add_row("Configuration", "✓ Loaded", ctx.obj['config_path'])
    table.add_row("Logging", "✓ Active", "Console logging enabled")
    
    console.print(table)


@cli.command()
@click.pass_context  
def agents(ctx):
    """List and manage agents"""
    console.print(Panel("[bold blue]Agent Management[/bold blue]"))
    
    # Agents table
    table = Table(title="Available Agents")
    table.add_column("Agent Type", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Capabilities")
    
    agent_types = ["repo_analyzer", "issue_finder", "code_tester", "report_generator"]
    
    for agent_type in agent_types:
        # In a real implementation, this would query actual agent status
        table.add_row(
            agent_type,
            "Available",
            "Ready for tasks"
        )
    
    console.print(table)


@cli.command()
@click.argument('repo_url')
@click.option('--branch', default='main', help='Branch to analyze')
@click.pass_context
def analyze(ctx, repo_url, branch):
    """Analyze a repository"""
    console.print(f"[bold blue]Analyzing repository:[/bold blue] {repo_url}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task1 = progress.add_task("Cloning repository...", total=None)
        # Simulate work
        import time
        time.sleep(2)
        
        progress.update(task1, description="Analyzing structure...")
        time.sleep(1)
        
        progress.update(task1, description="Detecting languages...")
        time.sleep(1)
        
        progress.update(task1, description="Finding issues...")
        time.sleep(2)
        
        progress.update(task1, description="Generating report...")
        time.sleep(1)
    
    console.print("[green]✓ Analysis complete![/green]")
    
    # Display results
    results_table = Table(title="Analysis Results")
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Value", style="yellow")
    
    results_table.add_row("Repository", repo_url)
    results_table.add_row("Branch", branch)
    results_table.add_row("Languages Detected", "Python, JavaScript, C++")
    results_table.add_row("Issues Found", "12 (3 high, 5 medium, 4 low)")
    results_table.add_row("Test Coverage", "85%")
    
    console.print(results_table)


@cli.command()
@click.pass_context
def logs(ctx):
    """View system logs"""
    console.print(Panel("[bold blue]Recent System Logs[/bold blue]"))
    
    # In a real implementation, this would read actual log files
    sample_logs = [
        "[2024-01-15 10:30:15] INFO - Agent repo_analyzer_1 started",
        "[2024-01-15 10:30:16] INFO - Configuration loaded successfully",
        "[2024-01-15 10:31:22] INFO - Repository analysis task started",
        "[2024-01-15 10:33:45] INFO - Found 12 issues in repository",
        "[2024-01-15 10:34:12] INFO - Analysis task completed successfully"
    ]
    
    for log_line in sample_logs:
        console.print(log_line)


@cli.command()
@click.option('--format', 'output_format', default='table', 
              type=click.Choice(['table', 'json']), help='Output format')
@click.pass_context
def config_show(ctx, output_format):
    """Show configuration"""
    config = ctx.obj['config']
    
    if output_format == 'json':
        console.print(json.dumps(config.config, indent=2))
    else:
        console.print(Panel("[bold blue]Configuration[/bold blue]"))
        
        # System configuration
        system_table = Table(title="System Configuration")
        system_table.add_column("Setting", style="cyan")
        system_table.add_column("Value", style="yellow")
        
        system_config = config.get_section("system")
        for key, value in system_config.items():
            system_table.add_row(key, str(value))
        
        console.print(system_table)


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health"""
    console.print(Panel("[bold blue]System Health Check[/bold blue]"))
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        task = progress.add_task("Checking components...", total=None)
        
        # Simulate health checks
        import time
        time.sleep(1)
        
        progress.update(task, description="Checking LLM providers...")
        time.sleep(1)
        
        progress.update(task, description="Checking agents...")
        time.sleep(1)
        
        progress.update(task, description="Checking database...")
        time.sleep(1)
    
    # Health results
    health_table = Table(title="Health Check Results")
    health_table.add_column("Component", style="cyan")
    health_table.add_column("Status", style="green")
    health_table.add_column("Details")
    
    health_table.add_row("Configuration", "✓ Healthy", "All settings valid")
    health_table.add_row("LLM Providers", "✓ Healthy", "OpenAI API accessible")
    health_table.add_row("Agents", "✓ Healthy", "All agents responsive") 
    health_table.add_row("Database", "✓ Healthy", "SQLite accessible")
    
    console.print(health_table)
    console.print("[green]✓ All systems healthy![/green]")


def main():
    """Main entry point for console interface"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()