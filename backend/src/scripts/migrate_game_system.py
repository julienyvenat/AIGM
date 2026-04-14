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
from src.engine.models import GameSystem, Universe
from sqlmodel import select
from sqlalchemy import text

SRD_RULES = """# SRD 5e Light - Résumé des Règles
**Mécanique de Résolution :**
- Toute action incertaine se résout par le jet d'un d20 auquel on ajoute le modificateur de la caractéristique appropriée (Force, Dextérité, Constitution, Intelligence, Sagesse, Charisme).
- Formule du modificateur : (Valeur de Caractéristique - 10) divisé par 2 (arrondi à l'inférieur).
- Le résultat total (d20 + modificateur) doit égaler ou dépasser le Degré de Difficulté (DD) fixé par le MJ, ou la Classe d'Armure (CA) de la cible en cas d'attaque.

**Avantage et Désavantage :**
- **Avantage :** Lancer deux d20 et garder le résultat le plus élevé.
- **Désavantage :** Lancer deux d20 et garder le résultat le plus bas.

**Combat et Santé :**
- La **CA (Classe d'Armure)** représente la difficulté à toucher physiquement un personnage.
- Les **PV (Points de Vie)** représentent la capacité d'encaissement. À 0 PV, un personnage est inconscient.
- **Dommages :** Les attaques réussies déduisent un montant variable de PV en fonction de l'arme ou du sort utilisé."""

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
        # 1. Vérifier si SRD 5e Light existe
        stmt = select(GameSystem).where(GameSystem.name == "SRD 5e Light")
        result = await session.execute(stmt)
        srd_system = result.scalars().first()

        if not srd_system:
            logger.info("GameSystem 'SRD 5e Light' not found. Creating it...")
            srd_system = GameSystem(
                name="SRD 5e Light",
                description="Système de jeu de rôle fantastique basé sur le d20. Inclut les mécaniques fondamentales du System Reference Document 5e.",
                rules_summary=SRD_RULES,
                dice_system="d20"
            )
            session.add(srd_system)
            await session.commit()
            await session.refresh(srd_system)
            logger.info(f"Created 'SRD 5e Light' with ID {srd_system.id}.")
        else:
            logger.info(f"GameSystem 'SRD 5e Light' already exists (ID: {srd_system.id}).")

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
