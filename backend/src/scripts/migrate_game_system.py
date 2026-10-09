import asyncio
import uuid
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend/src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.engine.database import init_db, engine, get_session
from src.engine.models import Universe
from src.engine.game_systems import ensure_default_game_systems
from sqlmodel import select
from sqlalchemy import text


async def migrate():
    logger.info("Starting GameSystem migration...")

    await init_db()

    # Manual schema migration for SQLite since Alembic is not configured
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE universe ADD COLUMN game_system_id CHAR(32) REFERENCES game_system (id)"))
            logger.info("Added game_system_id column to universe table.")
        except Exception as e:
            if "duplicate column name" in str(e):
                logger.info("game_system_id column already exists in universe table.")
            else:
                logger.warning(f"Could not add game_system_id column (it might already exist): {e}")

    async for session in get_session():
        # 1. Créer / mettre à jour le système par défaut (D&D SRD 5.2)
        srd_system = (await ensure_default_game_systems(session))[0]
        logger.info(f"GameSystem '{srd_system.name}' prêt (ID: {srd_system.id}).")

        # 2. Mettre à jour les univers sans game_system_id
        stmt_uni = select(Universe).where(Universe.game_system_id == None)
        result_uni = await session.execute(stmt_uni)
        universes = result_uni.scalars().all()

        if not universes:
            logger.info("No universes found needing migration.")
        else:
            logger.info(f"Found {len(universes)} universes without a GameSystem. Updating them...")
            for uni in universes:
                uni.game_system_id = srd_system.id
                session.add(uni)
            await session.commit()
            logger.info("Universes migrated successfully.")

        break # get_session() yields one session

    logger.info("Migration completed.")

if __name__ == "__main__":
    asyncio.run(migrate())
