"""
Base database interface and utilities.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData
import os


class Database(ABC):
    """Abstract base class for database operations."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.engine = None
        self.session_factory = None
        self.metadata = MetaData()
    
    @abstractmethod
    async def initialize(self):
        """Initialize database connection and create tables."""
        pass
    
    @abstractmethod
    async def close(self):
        """Close database connection."""
        pass
    
    @abstractmethod
    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        pass
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query."""
        async with self.get_session() as session:
            result = await session.execute(query, params or {})
            return [dict(row) for row in result]
    
    async def execute_transaction(self, operations: List[Dict[str, Any]]):
        """Execute multiple operations in a transaction."""
        async with self.get_session() as session:
            try:
                for operation in operations:
                    await session.execute(operation['query'], operation.get('params', {}))
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e


class SQLiteDatabase(Database):
    """SQLite database implementation."""
    
    def __init__(self, db_path: str):
        # Convert to async SQLite URL
        async_url = f"sqlite+aiosqlite:///{db_path}"
        super().__init__(async_url)
    
    async def initialize(self):
        """Initialize SQLite database."""
        self.engine = create_async_engine(
            self.connection_string,
            echo=False,
            future=True
        )
        
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(self.metadata.create_all)
    
    async def close(self):
        """Close SQLite database connection."""
        if self.engine:
            await self.engine.dispose()
    
    async def get_session(self) -> AsyncSession:
        """Get a SQLite database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()


class PostgreSQLDatabase(Database):
    """PostgreSQL database implementation."""
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
    
    async def initialize(self):
        """Initialize PostgreSQL database."""
        self.engine = create_async_engine(
            self.connection_string,
            echo=False,
            future=True,
            pool_size=10,
            max_overflow=20
        )
        
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(self.metadata.create_all)
    
    async def close(self):
        """Close PostgreSQL database connection."""
        if self.engine:
            await self.engine.dispose()
    
    async def get_session(self) -> AsyncSession:
        """Get a PostgreSQL database session."""
        if not self.session_factory:
            raise RuntimeError("Database not initialized")
        return self.session_factory()


def create_database(connection_string: str) -> Database:
    """Factory function to create appropriate database instance."""
    if connection_string.startswith('sqlite'):
        # Extract file path from SQLite URL
        db_path = connection_string.replace('sqlite:///', '')
        return SQLiteDatabase(db_path)
    elif connection_string.startswith('postgresql'):
        return PostgreSQLDatabase(connection_string)
    else:
        raise ValueError(f"Unsupported database type: {connection_string}")


class DatabaseManager:
    """Manager for multiple database connections."""
    
    _instance = None
    _databases: Dict[str, Database] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_database(self, name: str, database: Database):
        """Register a database instance."""
        self._databases[name] = database
    
    def get_database(self, name: str) -> Optional[Database]:
        """Get a registered database instance."""
        return self._databases.get(name)
    
    async def initialize_all(self):
        """Initialize all registered databases."""
        for name, database in self._databases.items():
            try:
                await database.initialize()
                print(f"Database '{name}' initialized successfully")
            except Exception as e:
                print(f"Failed to initialize database '{name}': {e}")
    
    async def close_all(self):
        """Close all registered databases."""
        for name, database in self._databases.items():
            try:
                await database.close()
                print(f"Database '{name}' closed successfully")
            except Exception as e:
                print(f"Failed to close database '{name}': {e}")
    
    def list_databases(self) -> List[str]:
        """List all registered database names."""
        return list(self._databases.keys())