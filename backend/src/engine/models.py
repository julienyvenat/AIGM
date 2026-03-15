import uuid
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

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
    name: str
    is_pc: bool = Field(default=False)
    hp: int
    max_hp: int
    armor_class: int
    speed: int
    x: int = Field(default=0)
    y: int = Field(default=0)

    items: List[Item] = Relationship(back_populates="character")
