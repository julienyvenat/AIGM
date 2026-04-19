import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.engine.models import GameSystem
from src.engine.database import engine

async def seed_dnd5e():
    from sqlmodel import SQLModel, Session
    from sqlalchemy.ext.asyncio import AsyncSession

    # Since database engine is async, we probably use async session
    async with AsyncSession(engine) as session:
        from sqlmodel import select
        # Check if D&D 5e already exists
        result = await session.execute(select(GameSystem).where(GameSystem.name == "D&D 5e"))
        existing = result.scalars().first()
        if existing:
            print("D&D 5e already exists in database.")
            return

        gs = GameSystem(
            name="D&D 5e",
            description="Dungeons & Dragons 5th Edition",
            rules_summary="A fantasy roleplaying game ruleset using the d20 system.",
            dice_system="d20",
            core_rules_prompt="Tu es un Arbitre (DM) pour D&D 5e. Toutes les résolutions d'action (combat, persuasion, escalade) utilisent un d20 + modificateur de caractéristique par rapport à une classe d'armure (CA/AC) ou un degré de difficulté (DD/DC). Les jets de sauvegarde s'effectuent de la même manière. Tu dois gérer les avantages (lance 2d20, garde le plus haut) et les désavantages (lance 2d20, garde le plus bas) selon la situation décrite par le Narrateur.",
            character_schema={
                "STR": "Force - Puissance physique",
                "DEX": "Dextérité - Agilité et réflexes",
                "CON": "Constitution - Santé et endurance",
                "INT": "Intelligence - Raisonnement et mémoire",
                "WIS": "Sagesse - Perception et intuition",
                "CHA": "Charisme - Force de personnalité",
                "HP": "Points de vie actuels",
                "AC": "Classe d'armure",
            }
        )
        session.add(gs)
        await session.commit()
        print("Successfully seeded D&D 5e game system.")

if __name__ == "__main__":
    asyncio.run(seed_dnd5e())
