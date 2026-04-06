from sqlalchemy import create_engine
from src.engine.models import SQLModel
engine = create_engine("sqlite:///rpg_database.db", echo=True)
SQLModel.metadata.create_all(engine)
