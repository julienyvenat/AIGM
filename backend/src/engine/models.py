import uuid
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

class ChatMessage(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    player_id: Optional[str] = Field(default=None, index=True)
    sender: str
    type: str
    category: Optional[str] = Field(default=None)
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Item(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    character_id: uuid.UUID = Field(foreign_key="character.id")
    name: str
    item_type: str
    damage_dice: Optional[str] = Field(default=None)
    quantity: int = Field(default=1)

    character: Optional["Character"] = Relationship(back_populates="items")

class Character(SQLModel, table=True):
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

class WorldNPCTable(SQLModel, table=True):
    __tablename__ = "world_npc"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id")
    nom: str
    faction: Optional[str] = Field(default=None)
    description: str
    hp: Optional[int] = Field(default=None)
    armor_class: Optional[int] = Field(default=None)
    x: int = Field(default=0)
    y: int = Field(default=0)
    is_in_combat: bool = Field(default=False)

    universe: Optional["Universe"] = Relationship(back_populates="npcs")

class WorldLocationTable(SQLModel, table=True):
    __tablename__ = "world_location"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id")
    nom: str
    description: str
    points_interet: str = Field(default="[]")

    universe: Optional["Universe"] = Relationship(back_populates="locations")

class WorldFactionTable(SQLModel, table=True):
    __tablename__ = "world_faction"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id")
    nom: str
    description: str
    relations_politiques: str = Field(default="[]")

    universe: Optional["Universe"] = Relationship(back_populates="factions")

class Universe(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    description: str
    image_url: Optional[str] = Field(default=None)

    characters: List[Character] = Relationship(back_populates="universe")
    npcs: List[WorldNPCTable] = Relationship(back_populates="universe")
    locations: List[WorldLocationTable] = Relationship(back_populates="universe")
    factions: List[WorldFactionTable] = Relationship(back_populates="universe")
    sessions: List["GameSession"] = Relationship(back_populates="universe")

class GameSession(SQLModel, table=True):
    __tablename__ = "game_session"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    universe_id: uuid.UUID = Field(foreign_key="universe.id")
    status: GameSessionStatus = Field(default=GameSessionStatus.LOBBY)
    current_battlemap_url: Optional[str] = Field(default=None)
    game_mode: str = Field(default="NARRATIVE")

    universe: Optional["Universe"] = Relationship(back_populates="sessions")
    participants: List[Character] = Relationship(back_populates="game_sessions", link_model=SessionParticipants)
