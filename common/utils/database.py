"""
Database management for the AI Agent System.

Provides database connection management, schema definitions,
and data access patterns using SQLAlchemy.
"""

import asyncio
from typing import Dict, Any, Optional, List, Type, Union
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import json

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Text, Boolean, 
    JSON, Float, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import QueuePool
from alembic import command
from alembic.config import Config as AlembicConfig

from .logger import Logger

Base = declarative_base()


class AuditRun(Base):
    """Audit run tracking."""
    __tablename__ = "audit_runs"
    
    id = Column(Integer, primary_key=True)
    repository_url = Column(String(512), nullable=False)
    branch = Column(String(128), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_issues = Column(Integer, default=0)
    high_priority_issues = Column(Integer, default=0)
    config = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    issues = relationship("Issue", back_populates="audit_run", cascade="all, delete-orphan")
    fixes = relationship("CodeFix", back_populates="audit_run", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_audit_runs_status', 'status'),
        Index('idx_audit_runs_repository', 'repository_url'),
    )


class Issue(Base):
    """Code issue detected during analysis."""
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True)
    audit_run_id = Column(Integer, ForeignKey("audit_runs.id"), nullable=False)
    
    # Issue identification
    type = Column(String(100), nullable=False)  # bug, performance, security, etc.
    severity = Column(String(20), nullable=False)  # critical, high, medium, low
    priority = Column(String(20), nullable=False)  # high, medium, low
    
    # Location information
    file_path = Column(String(1024), nullable=False)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    column_start = Column(Integer, nullable=True)
    column_end = Column(Integer, nullable=True)
    
    # Issue details
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    code_snippet = Column(Text, nullable=True)
    detection_method = Column(String(100), nullable=True)  # static_analysis, llm_analysis, etc.
    
    # Status tracking
    status = Column(String(50), default="open")  # open, fixed, dismissed, duplicate
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional metadata
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    audit_run = relationship("AuditRun", back_populates="issues")
    fixes = relationship("CodeFix", back_populates="issue")
    
    __table_args__ = (
        Index('idx_issues_audit_run', 'audit_run_id'),
        Index('idx_issues_severity', 'severity'),
        Index('idx_issues_type', 'type'),
        Index('idx_issues_status', 'status'),
    )


class CodeFix(Base):
    """Code fix generated for an issue."""
    __tablename__ = "code_fixes"
    
    id = Column(Integer, primary_key=True)
    audit_run_id = Column(Integer, ForeignKey("audit_runs.id"), nullable=False)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=True)
    
    # Fix details
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    fix_type = Column(String(100), nullable=False)  # bug_fix, performance_improvement, etc.
    
    # File changes
    file_path = Column(String(1024), nullable=False)
    original_code = Column(Text, nullable=True)
    fixed_code = Column(Text, nullable=False)
    diff = Column(Text, nullable=True)
    
    # Testing information
    tested = Column(Boolean, default=False)
    test_results = Column(JSON, nullable=True)
    performance_impact = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(String(50), default="proposed")  # proposed, tested, approved, committed, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    commit_hash = Column(String(64), nullable=True)
    
    # Relationships
    audit_run = relationship("AuditRun", back_populates="fixes")
    issue = relationship("Issue", back_populates="fixes")
    
    __table_args__ = (
        Index('idx_code_fixes_audit_run', 'audit_run_id'),
        Index('idx_code_fixes_issue', 'issue_id'),
        Index('idx_code_fixes_status', 'status'),
    )


class AgentTask(Base):
    """Individual agent task tracking."""
    __tablename__ = "agent_tasks"
    
    id = Column(Integer, primary_key=True)
    audit_run_id = Column(Integer, ForeignKey("audit_runs.id"), nullable=True)
    
    # Task identification
    agent_name = Column(String(100), nullable=False)
    task_type = Column(String(100), nullable=False)
    task_id = Column(String(128), nullable=False, unique=True)
    
    # Task parameters
    parameters = Column(JSON, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    
    # Status tracking
    status = Column(String(50), default="pending")  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Resource usage
    memory_usage_mb = Column(Float, nullable=True)
    cpu_time_seconds = Column(Float, nullable=True)
    
    # Progress tracking
    progress_percentage = Column(Float, default=0.0)
    progress_message = Column(String(512), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_agent_tasks_status', 'status'),
        Index('idx_agent_tasks_agent', 'agent_name'),
        Index('idx_agent_tasks_audit_run', 'audit_run_id'),
    )


class LLMUsageLog(Base):
    """LLM usage tracking and cost monitoring."""
    __tablename__ = "llm_usage_logs"
    
    id = Column(Integer, primary_key=True)
    audit_run_id = Column(Integer, ForeignKey("audit_runs.id"), nullable=True)
    agent_task_id = Column(Integer, ForeignKey("agent_tasks.id"), nullable=True)
    
    # Provider and model info
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    
    # Usage statistics
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Cost tracking
    estimated_cost = Column(Float, default=0.0)
    
    # Performance metrics
    latency_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Request details
    request_type = Column(String(100), nullable=True)  # analysis, fix_generation, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_llm_usage_provider', 'provider'),
        Index('idx_llm_usage_date', 'created_at'),
        Index('idx_llm_usage_audit_run', 'audit_run_id'),
    )


class SystemMetrics(Base):
    """System performance and health metrics."""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True)
    
    # System metrics
    cpu_usage_percent = Column(Float, nullable=True)
    memory_usage_percent = Column(Float, nullable=True)
    disk_usage_percent = Column(Float, nullable=True)
    
    # Agent metrics
    active_agents = Column(Integer, default=0)
    queued_tasks = Column(Integer, default=0)
    failed_tasks_1h = Column(Integer, default=0)
    
    # LLM metrics
    llm_requests_1h = Column(Integer, default=0)
    llm_errors_1h = Column(Integer, default=0)
    llm_cost_today = Column(Float, default=0.0)
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_system_metrics_date', 'recorded_at'),
    )


class DatabaseManager:
    """Database manager with connection pooling and async support."""
    
    def __init__(self, database_url: str, echo: bool = False):
        self.database_url = database_url
        self.echo = echo
        self.logger = Logger("DatabaseManager")
        
        # Sync engine for migrations and initial setup
        self.sync_engine = None
        self.sync_session_factory = None
        
        # Async engine for operations
        self.async_engine = None
        self.async_session_factory = None
        
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize database connections and create tables."""
        try:
            # Setup sync engine for migrations
            self.sync_engine = create_engine(
                self.database_url,
                echo=self.echo,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600
            )
            
            self.sync_session_factory = sessionmaker(bind=self.sync_engine)
            
            # Setup async engine for operations
            if self.database_url.startswith("sqlite"):
                async_url = self.database_url.replace("sqlite://", "sqlite+aiosqlite://")
            elif self.database_url.startswith("postgresql"):
                async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")
            else:
                async_url = self.database_url
            
            self.async_engine = create_async_engine(
                async_url,
                echo=self.echo,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600
            )
            
            self.async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            await self.create_tables()
            
            self.is_initialized = True
            self.logger.info("Database manager initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {str(e)}")
            return False
    
    async def create_tables(self):
        """Create database tables."""
        try:
            # Use sync engine to create tables
            Base.metadata.create_all(self.sync_engine)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create tables: {str(e)}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session with automatic cleanup."""
        if not self.is_initialized:
            raise RuntimeError("Database manager not initialized")
        
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def create_audit_run(self, repository_url: str, branch: str, config: Optional[Dict] = None) -> int:
        """Create a new audit run."""
        async with self.get_session() as session:
            audit_run = AuditRun(
                repository_url=repository_url,
                branch=branch,
                config=config or {}
            )
            session.add(audit_run)
            await session.flush()
            return audit_run.id
    
    async def update_audit_run_status(self, audit_run_id: int, status: str, error_message: Optional[str] = None):
        """Update audit run status."""
        async with self.get_session() as session:
            audit_run = await session.get(AuditRun, audit_run_id)
            if audit_run:
                audit_run.status = status
                if status in ["completed", "failed"]:
                    audit_run.completed_at = datetime.utcnow()
                if error_message:
                    audit_run.error_message = error_message
                await session.flush()
    
    async def create_issue(self, audit_run_id: int, issue_data: Dict[str, Any]) -> int:
        """Create a new issue."""
        async with self.get_session() as session:
            issue = Issue(audit_run_id=audit_run_id, **issue_data)
            session.add(issue)
            await session.flush()
            return issue.id
    
    async def create_code_fix(self, audit_run_id: int, fix_data: Dict[str, Any]) -> int:
        """Create a new code fix."""
        async with self.get_session() as session:
            code_fix = CodeFix(audit_run_id=audit_run_id, **fix_data)
            session.add(code_fix)
            await session.flush()
            return code_fix.id
    
    async def create_agent_task(self, task_data: Dict[str, Any]) -> int:
        """Create a new agent task."""
        async with self.get_session() as session:
            task = AgentTask(**task_data)
            session.add(task)
            await session.flush()
            return task.id
    
    async def update_agent_task(self, task_id: int, **updates):
        """Update agent task."""
        async with self.get_session() as session:
            task = await session.get(AgentTask, task_id)
            if task:
                for key, value in updates.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                task.updated_at = datetime.utcnow()
                await session.flush()
    
    async def log_llm_usage(self, usage_data: Dict[str, Any]):
        """Log LLM usage."""
        async with self.get_session() as session:
            usage_log = LLMUsageLog(**usage_data)
            session.add(usage_log)
            await session.flush()
    
    async def record_system_metrics(self, metrics: Dict[str, Any]):
        """Record system metrics."""
        async with self.get_session() as session:
            system_metrics = SystemMetrics(**metrics)
            session.add(system_metrics)
            await session.flush()
    
    async def get_audit_run_stats(self, audit_run_id: int) -> Optional[Dict[str, Any]]:
        """Get statistics for an audit run."""
        async with self.get_session() as session:
            audit_run = await session.get(AuditRun, audit_run_id)
            if not audit_run:
                return None
            
            # Count issues by severity
            from sqlalchemy import func, select
            
            issue_counts = await session.execute(
                select(Issue.severity, func.count(Issue.id))
                .where(Issue.audit_run_id == audit_run_id)
                .group_by(Issue.severity)
            )
            
            severity_counts = dict(issue_counts.fetchall())
            
            # Count fixes by status
            fix_counts = await session.execute(
                select(CodeFix.status, func.count(CodeFix.id))
                .where(CodeFix.audit_run_id == audit_run_id)
                .group_by(CodeFix.status)
            )
            
            fix_status_counts = dict(fix_counts.fetchall())
            
            return {
                "audit_run": audit_run,
                "severity_counts": severity_counts,
                "fix_status_counts": fix_status_counts
            }
    
    async def get_recent_audit_runs(self, limit: int = 10) -> List[AuditRun]:
        """Get recent audit runs."""
        async with self.get_session() as session:
            from sqlalchemy import select, desc
            
            result = await session.execute(
                select(AuditRun)
                .order_by(desc(AuditRun.started_at))
                .limit(limit)
            )
            
            return result.scalars().all()
    
    async def get_llm_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get LLM usage statistics."""
        async with self.get_session() as session:
            from sqlalchemy import func, select
            
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # Total usage by provider
            provider_stats = await session.execute(
                select(
                    LLMUsageLog.provider,
                    func.sum(LLMUsageLog.total_tokens).label("total_tokens"),
                    func.sum(LLMUsageLog.estimated_cost).label("total_cost"),
                    func.count(LLMUsageLog.id).label("request_count")
                )
                .where(LLMUsageLog.created_at >= since_date)
                .group_by(LLMUsageLog.provider)
            )
            
            return {
                "provider_stats": dict(provider_stats.fetchall()),
                "period_days": days
            }
    
    async def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old data."""
        async with self.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old system metrics
            await session.execute(
                SystemMetrics.__table__.delete()
                .where(SystemMetrics.recorded_at < cutoff_date)
            )
            
            # Delete old LLM usage logs
            await session.execute(
                LLMUsageLog.__table__.delete()
                .where(LLMUsageLog.created_at < cutoff_date)
            )
            
            await session.flush()
            self.logger.info(f"Cleaned up data older than {days_to_keep} days")
    
    async def close(self):
        """Close database connections."""
        if self.async_engine:
            await self.async_engine.dispose()
        
        if self.sync_engine:
            self.sync_engine.dispose()
        
        self.is_initialized = False
        self.logger.info("Database connections closed")