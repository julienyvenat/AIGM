from pydantic import BaseModel, Field
from typing import List, Optional

class WorldNPC(BaseModel):
    nom: str = Field(description="Nom du PNJ")
    faction: Optional[str] = Field(default=None, description="Faction à laquelle appartient le PNJ")
    description: str = Field(description="Description détaillée du PNJ (apparence, personnalité, histoire)")
    hp: Optional[int] = Field(default=None, description="Points de vie (HP) s'ils sont mentionnés")
    armor_class: Optional[int] = Field(default=None, description="Classe d'armure (AC) si mentionnée")

class WorldLocation(BaseModel):
    nom: str = Field(description="Nom du lieu")
    description: str = Field(description="Description détaillée du lieu (ambiance, géographie, histoire)")
    points_interet: List[str] = Field(default_factory=list, description="Liste des points d'intérêt dans ce lieu")

class WorldFaction(BaseModel):
    nom: str = Field(description="Nom de la faction")
    description: str = Field(description="Description détaillée de la faction (buts, membres, idéologie)")
    relations_politiques: List[str] = Field(default_factory=list, description="Relations avec les autres factions ou entités")

class WorldKnowledge(BaseModel):
    npc: List[WorldNPC] = Field(default_factory=list, description="Liste des PNJ extraits")
    location: List[WorldLocation] = Field(default_factory=list, description="Liste des lieux extraits")
    faction: List[WorldFaction] = Field(default_factory=list, description="Liste des factions extraites")
    histoire_globale: str = Field(default="", description="Tout le reste du texte : légendes, histoire générale, ambiance globale, événements passés, qui ne rentrent pas dans les entités spécifiques.")
