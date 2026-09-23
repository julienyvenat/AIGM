import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

# Default: SQLite, for zero-friction local dev/tests (unchanged behavior).
# Production sets DATABASE_URL (e.g. to a Postgres DSN) via the environment
# -- see docker-compose.prod.yml / .env.production.example. This must stay
# an async driver URL (e.g. `postgresql+asyncpg://...`, not plain
# `postgresql://...`) since the rest of the app uses the SQLAlchemy async
# API throughout.
DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///./rpg_database.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)


def _make_engine(url: str):
    # NullPool: don't keep pooled connections around between requests. This
    # matters most for aiosqlite -- a pooled connection is tied to the
    # asyncio event loop it was created on, and reusing it from a different
    # loop (e.g. successive TestClient instances in the test suite, each of
    # which runs its own event loop) hangs forever instead of raising.
    # Opening a fresh connection per checkout avoids that class of bug
    # entirely. For Postgres in production this trades a little connection
    # setup latency for the same simplicity/safety; with a single small NAS
    # deployment and a handful of players this is a non-issue. Revisit with
    # a real pool (or pgbouncer) only if connection churn becomes a
    # measurable problem.
    return create_async_engine(url, echo=True, future=True, poolclass=NullPool)


engine = _make_engine(DATABASE_URL)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
