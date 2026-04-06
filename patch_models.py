import re

with open("backend/src/engine/models.py", "r") as f:
    content = f.read()

new_imports = """import uuid
from datetime import datetime
from typing import List, Optional
from enum import Enum
from sqlmodel import Field, Relationship, SQLModel

class GameSessionStatus(str, Enum):
    LOBBY = "LOBBY"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"

class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str

    characters: List["Character"] = Relationship(back_populates="user")

class SessionParticipants(SQLModel, table=True):
    character_id: uuid.UUID = Field(foreign_key="character.id", primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="game_session.id", primary_key=True)
"""

content = re.sub(r'import uuid\nfrom datetime import datetime\nfrom typing import List, Optional\nfrom sqlmodel import Field, Relationship, SQLModel\n', new_imports, content)

char_repl = r"""class Character(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id")
    user_id: Optional[uuid.UUID] = Field(default=None, foreign_key="user.id")
    name: str
    is_pc: bool = Field(default=False)
    hp: int
    max_hp: int
    armor_class: int
    speed: int
    x: int = Field(default=0)
    y: int = Field(default=0)
    reference_portrait_url: Optional[str] = Field(default=None)
    strength: int = Field(default=10)
    dexterity: int = Field(default=10)
    constitution: int = Field(default=10)
    intelligence: int = Field(default=10)
    wisdom: int = Field(default=10)
    charisma: int = Field(default=10)
    level: int = Field(default=1)
    experience: int = Field(default=0)

    known_spells: str = Field(default="[]")
    spell_slots: str = Field(default="{}")
    class_resources: str = Field(default="{}")

    items: List[Item] = Relationship(back_populates="character")
    universe: Optional["Universe"] = Relationship(back_populates="characters")
    user: Optional[User] = Relationship(back_populates="characters")
    game_sessions: List["GameSession"] = Relationship(back_populates="participants", link_model=SessionParticipants)
"""

content = re.sub(r'class Character\(SQLModel, table=True\):.*?    universe: Optional\["Universe"\] = Relationship\(back_populates="characters"\)\n', char_repl, content, flags=re.DOTALL)


gamesession_def = r"""
class GameSession(SQLModel, table=True):
    __tablename__ = "game_session"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id")
    status: GameSessionStatus = Field(default=GameSessionStatus.LOBBY)
    current_battlemap_url: Optional[str] = Field(default=None)
    game_mode: str = Field(default="NARRATIVE")

    universe: Optional["Universe"] = Relationship(back_populates="sessions")
    participants: List[Character] = Relationship(back_populates="game_sessions", link_model=SessionParticipants)
"""

content += gamesession_def

universe_repl = r"""    factions: List[WorldFactionTable] = Relationship(back_populates="universe")
    sessions: List[GameSession] = Relationship(back_populates="universe")"""

content = content.replace('    factions: List[WorldFactionTable] = Relationship(back_populates="universe")', universe_repl)

with open("backend/src/engine/models.py", "w") as f:
    f.write(content)
