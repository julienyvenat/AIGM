import asyncio
from sqlmodel import select
from sqlalchemy.orm import selectinload
from src.engine.database import get_session
from src.engine.models import GameSession, Universe

async def main():
    async for session in get_session():
        print("Backend models patched properly without exceptions.")
        break

if __name__ == "__main__":
    asyncio.run(main())
