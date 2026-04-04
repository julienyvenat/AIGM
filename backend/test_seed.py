import asyncio
from sqlmodel import SQLModel, Session, create_engine
from src.engine.models import Character

engine = create_engine("sqlite:///database.db")

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def seed():
    with Session(engine) as session:
        char = Character(
            name="Thorin",
            is_pc=True,
            hp=25,
            max_hp=30,
            armor_class=16,
            speed=25,
            strength=16,
            dexterity=12,
            constitution=14,
            intelligence=10,
            wisdom=13,
            charisma=9,
            level=3,
            experience=1500,
            known_spells='[{"name": "Coup puissant", "description": "Attaque forte"}]',
            spell_slots='{"level_1": {"max": 3, "used": 1}}',
            class_resources='{"Rage": {"max": 2, "used": 0}}'
        )
        session.add(char)
        session.commit()

if __name__ == "__main__":
    create_db_and_tables()
    seed()
