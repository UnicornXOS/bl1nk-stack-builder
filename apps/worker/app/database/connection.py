"""
Database connection and management for bl1nk-agent-builder
Handles PostgreSQL + pgvector connections with async support
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Pool, Connection

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Global connection pool
_db_pool: Optional[Pool] = None


async def init_db() -> None:
    """Initialize database connection pool"""
    global _db_pool
    
    logger.info("Initializing database connection pool...")
    
    try:
        _db_pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=settings.db_pool_min,
            max_size=settings.db_pool_max,
            command_timeout=settings.db_pool_timeout,
            server_settings={
                "jit": "off",  # Disable JIT for better stability
            }
        )
        
        # Test connection
        async with _db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        logger.info(f"Database connection pool initialized (min={settings.db_pool_min}, max={settings.db_pool_max})")
        
    except Exception as e:
        logger.error(f"Failed to initialize database connection pool: {e}")
        raise


async def close_db() -> None:
    """Close database connection pool"""
    global _db_pool
    
    if _db_pool:
        logger.info("Closing database connection pool...")
        await _db_pool.close()
        _db_pool = None
        logger.info("Database connection pool closed")


@asynccontextmanager
async def get_db() -> AsyncGenerator[Connection, None]:
    """Get database connection from pool"""
    if not _db_pool:
        raise RuntimeError("Database connection pool not initialized")
    
    async with _db_pool.acquire() as connection:
        try:
            yield connection
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise


async def execute_query(query: str, *args) -> str:
    """Execute a query and return the status"""
    async with get_db() as conn:
        return await conn.execute(query, *args)


async def fetch_one(query: str, *args) -> Optional[dict]:
    """Fetch a single row"""
    async with get_db() as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def fetch_many(query: str, *args) -> list[dict]:
    """Fetch multiple rows"""
    async with get_db() as conn:
        rows = await conn.fetch(query, *args)
        return [dict(row) for row in rows]


async def fetch_val(query: str, *args):
    """Fetch a single value"""
    async with get_db() as conn:
        return await conn.fetchval(query, *args)


async def create_tables() -> None:
    """Create all database tables from migrations"""
    logger.info("Creating database tables...")
    
    # Read and execute migration files
    migration_files = [
        "sql/migrations/001_create_tables.sql",
        "sql/migrations/002_add_indexes.sql"
    ]
    
    for migration_file in migration_files:
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
            
            async with get_db() as conn:
                async with conn.transaction():
                    for statement in statements:
                        if statement:
                            await conn.execute(statement)
            
            logger.info(f"Applied migration: {migration_file}")
            
        except FileNotFoundError:
            logger.warning(f"Migration file not found: {migration_file}")
        except Exception as e:
            logger.error(f"Failed to apply migration {migration_file}: {e}")
            raise


async def health_check() -> dict:
    """Check database health"""
    try:
        async with get_db() as conn:
            # Check basic connectivity
            result = await conn.fetchval("SELECT 1")
            
            # Check pgvector extension
            pgvector_check = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
            )
            
            # Check table counts
            table_counts = {}
            tables = ['users', 'tasks', 'documents', 'embeddings']
            
            for table in tables:
                try:
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                    table_counts[table] = count
                except Exception:
                    table_counts[table] = "error"
            
            return {
                "status": "healthy",
                "connection": "ok" if result == 1 else "failed",
                "pgvector": "installed" if pgvector_check else "missing",
                "tables": table_counts
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }