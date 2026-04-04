import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

sqlite_url = "sqlite+aiosqlite:///./rpg_database.db"
engine = create_async_engine(sqlite_url, echo=True, future=True)

async def migrate():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE character ADD COLUMN game_mode VARCHAR NOT NULL DEFAULT 'NARRATIVE'"))
            await conn.execute(text("ALTER TABLE character ADD COLUMN battlemap_image_url VARCHAR"))
            print("Added columns to Character")
        except Exception as e:
            print(f"Error altering character: {e}")

        try:
            await conn.execute(text("ALTER TABLE world_npc ADD COLUMN x INTEGER NOT NULL DEFAULT 0"))
            await conn.execute(text("ALTER TABLE world_npc ADD COLUMN y INTEGER NOT NULL DEFAULT 0"))
            await conn.execute(text("ALTER TABLE world_npc ADD COLUMN is_in_combat BOOLEAN NOT NULL DEFAULT 0"))
            print("Added columns to WorldNPCTable")
        except Exception as e:
            print(f"Error altering world_npc: {e}")

asyncio.run(migrate())
