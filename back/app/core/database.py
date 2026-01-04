from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import settings
from typing import AsyncGenerator, Generator


class DatabaseManager:
    def __init__(self):
        # Master database (read/write)
        self.engine_master = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_size=settings.POSTGRES_POOL_SIZE,
            max_overflow=settings.POSTGRES_MAX_OVERFLOW,
            pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
            pool_recycle=settings.POSTGRES_POOL_RECYCLE,
            poolclass=QueuePool,
        )

        self.async_session_master = async_sessionmaker(
            self.engine_master,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        # Синхронный движок для Celery задач
        sync_url = settings.DATABASE_URL.replace('+asyncpg', '').replace('postgresql+asyncpg', 'postgresql')
        self.sync_engine = create_engine(
            sync_url,
            echo=settings.DEBUG,
            pool_size=settings.POSTGRES_POOL_SIZE,
            max_overflow=settings.POSTGRES_MAX_OVERFLOW,
            pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
            pool_recycle=settings.POSTGRES_POOL_RECYCLE,
            poolclass=QueuePool,
        )

        self.sync_session_maker = sessionmaker(
            self.sync_engine,
            class_=Session,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        # Replica database (read-only) for search queries
        self.engine_replica = None
        self.async_session_replica = None

        if settings.POSTGRES_REPLICA_ENABLED and settings.DATABASE_URL_REPLICA:
            self.engine_replica = create_async_engine(
                settings.DATABASE_URL_REPLICA,
                echo=settings.DEBUG,
                pool_size=settings.POSTGRES_POOL_SIZE,
                max_overflow=settings.POSTGRES_MAX_OVERFLOW,
                pool_timeout=settings.POSTGRES_POOL_TIMEOUT,
                pool_recycle=settings.POSTGRES_POOL_RECYCLE,
                poolclass=QueuePool,
            )

            self.async_session_replica = async_sessionmaker(
                self.engine_replica,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session for write operations."""
        async with self.async_session_master() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def get_read_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session for read operations (uses replica if available)."""
        session_maker = (
            self.async_session_replica
            if self.async_session_replica
            else self.async_session_master
        )

        async with session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

    def get_sync_session(self) -> Generator[Session, None, None]:
        """Get synchronous database session for Celery tasks."""
        session = self.sync_session_maker()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def close(self):
        """Close database connections."""
        await self.engine_master.dispose()
        if self.engine_replica:
            await self.engine_replica.dispose()
        if self.sync_engine:
            self.sync_engine.dispose()


db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session."""
    async for session in db_manager.get_session():
        yield session


async def get_read_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for read-only database session."""
    async for session in db_manager.get_read_session():
        yield session


def get_sync_db() -> Generator[Session, None, None]:
    """Dependency for synchronous database session (Celery tasks)."""
    yield from db_manager.get_sync_session()
