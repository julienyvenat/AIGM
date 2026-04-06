import asyncio
import uuid
import logging
import sys
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add backend/src to sys.path so it resolves imports correctly when executed from anywhere
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from src.memory.vector_db import add_to_memory
from src.engine.database import init_db, get_session
from src.engine.models import Character, Item

async def main():
    logger.info("Starting seed script...")

    # 1. Initialize the SQL database
    logger.info("Initializing the database tables...")
    await init_db()

    # 2. Fill the RAG Memory
    logger.info("Injecting RAG Memory (Lore and Scenario)...")
    lore_text = "Le monde de jeu est un univers dark fantasy. La magie est rare et dangereuse."
    scenario_text = "Le joueur principal se réveille dans les cachots humides du Château Noir. Un gobelin chétif mais agressif monte la garde devant la porte de la cellule."

    await add_to_memory(lore_text, memory_type="lore")
    await add_to_memory(scenario_text, memory_type="scenario")
    logger.info("RAG memory injected successfully.")

    # 3. Fill the SQL Database (Characters and Items)
    logger.info("Injecting SQL Entities (Characters and Items)...")

    # Generate fixed UUIDs or just new ones
    aragorn_id = uuid.uuid4()
    goblin_id = uuid.uuid4()

    # Create Player (Aragorn)
    aragorn = Character(
        id=aragorn_id,
        name="Aragorn",
        is_pc=True,
        hp=20,
        max_hp=20,
        armor_class=14,
        speed=6,
        x=2,
        y=2
    )

    # Create Player's Item (Longsword)
    longsword = Item(
        character_id=aragorn_id,
        name="Épée longue",
        item_type="weapon",
        damage_dice="1d8",
        quantity=1
    )

    # Create Monster (Goblin)
    goblin = Character(
        id=goblin_id,
        name="Gobelin Gardien",
        is_pc=False,
        hp=7,
        max_hp=7,
        armor_class=11,
        speed=6,
        x=4,
        y=4
    )

    # Insert into the database
    async for session in get_session():
        session.add(aragorn)
        session.add(longsword)
        session.add(goblin)
        await session.commit()
        break # get_session() yields one session, so we break after using it

    logger.info("SQL entities injected successfully.")

    print("\n" + "="*50)
    print("SEED SCRIPT COMPLETED SUCCESSFULLY")
    print("="*50)
    print(f"!!! IMPORTANT !!!")
    print(f"Use this UUID in the frontend for Aragorn: {aragorn_id}")
    print("="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
