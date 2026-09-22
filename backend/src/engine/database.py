from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlmodel import SQLModel

sqlite_url = "sqlite+aiosqlite:///./rpg_database.db"

# NullPool: don't keep pooled aiosqlite connections around between requests.
# A pooled connection is tied to the asyncio event loop it was created on;
# reusing it from a different loop (e.g. successive TestClient instances in
# the test suite, each of which runs its own event loop) hangs forever
# instead of raising. Opening a fresh connection per checkout avoids that
# class of bug entirely, at a negligible cost for this SQLite-backed app.
engine = create_async_engine(sqlite_url, echo=True, future=True, poolclass=NullPool)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
