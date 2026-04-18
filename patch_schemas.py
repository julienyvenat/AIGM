from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
import uuid
import inspect
import sys
import os

sys.path.insert(0, os.path.abspath('backend'))
from src.engine.models import GameSystem, Universe, GameSession

print(GameSession.__annotations__)
