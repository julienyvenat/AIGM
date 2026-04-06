from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from typing import List
from pydantic import BaseModel
import uuid

from engine.database import get_session
from engine.models import Universe, WorldNPCTable, WorldLocationTable, WorldFactionTable, Character
from agents.universe_architect import generate_universe_from_prompt
from memory.vector_db import add_to_memory

router = APIRouter()

class UniverseGenerateRequest(BaseModel):
    prompt: str

@router.post("/world/generate-from-prompt")
async def generate_universe(req: UniverseGenerateRequest, db: AsyncSession = Depends(get_session)):
    # Create the universe and its entities
    universe, world_knowledge = await generate_universe_from_prompt(req.prompt, db)

    # Save the global lore to ChromaDB with universe_id metadata
    await add_to_memory(
        text=world_knowledge.histoire_globale,
        memory_type="lore",
        metadata={"universe_id": str(universe.id), "entity_type": "global_history"}
    )

    # Save NPCs to ChromaDB
    for npc in world_knowledge.npc:
        await add_to_memory(
            text=f"{npc.nom} ({npc.faction or 'Sans faction'}): {npc.description}",
            memory_type="lore",
            metadata={"universe_id": str(universe.id), "entity_type": "NPC", "name": npc.nom}
        )

    # Save Locations to ChromaDB
    for loc in world_knowledge.location:
        await add_to_memory(
            text=f"{loc.nom}: {loc.description}. Points d'intérêt: {', '.join(loc.points_interet)}",
            memory_type="lore",
            metadata={"universe_id": str(universe.id), "entity_type": "Location", "name": loc.nom}
        )

    # Save Factions to ChromaDB
    for fact in world_knowledge.faction:
        await add_to_memory(
            text=f"{fact.nom}: {fact.description}. Relations: {', '.join(fact.relations_politiques)}",
            memory_type="lore",
            metadata={"universe_id": str(universe.id), "entity_type": "Faction", "name": fact.nom}
        )

    return {"status": "success", "universe": universe}

@router.get("/universes", response_model=List[Universe])
async def get_universes(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Universe))
    return result.scalars().all()

@router.get("/universes/{universe_id}", response_model=Universe)
async def get_universe(universe_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    universe = await db.get(Universe, universe_id)
    if not universe:
        raise HTTPException(status_code=404, detail="Universe not found")
    return universe

# CRUD Endpoints for entities within a universe
@router.get("/universes/{universe_id}/npcs", response_model=List[WorldNPCTable])
async def get_npcs(universe_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(WorldNPCTable).where(WorldNPCTable.universe_id == universe_id))
    return result.scalars().all()

@router.get("/universes/{universe_id}/locations", response_model=List[WorldLocationTable])
async def get_locations(universe_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(WorldLocationTable).where(WorldLocationTable.universe_id == universe_id))
    return result.scalars().all()

@router.get("/universes/{universe_id}/factions", response_model=List[WorldFactionTable])
async def get_factions(universe_id: uuid.UUID, db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(WorldFactionTable).where(WorldFactionTable.universe_id == universe_id))
    return result.scalars().all()

# Updating an NPC
class NPCPatch(BaseModel):
    nom: str
    faction: str | None
    description: str

@router.put("/npcs/{npc_id}")
async def update_npc(npc_id: uuid.UUID, req: NPCPatch, db: AsyncSession = Depends(get_session)):
    npc = await db.get(WorldNPCTable, npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")
    npc.nom = req.nom
    npc.faction = req.faction
    npc.description = req.description
    await db.commit()
    return npc

# Updating a Faction
class FactionPatch(BaseModel):
    nom: str
    description: str

@router.put("/factions/{faction_id}")
async def update_faction(faction_id: uuid.UUID, req: FactionPatch, db: AsyncSession = Depends(get_session)):
    faction = await db.get(WorldFactionTable, faction_id)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")
    faction.nom = req.nom
    faction.description = req.description
    await db.commit()
    return faction

# Fetching characters by Universe AND Name
@router.get("/universes/{universe_id}/characters/by-name/{name}", response_model=Character)
async def get_or_create_character_by_universe(universe_id: uuid.UUID, name: str, db: AsyncSession = Depends(get_session)):
    universe = await db.get(Universe, universe_id)
    if not universe:
        raise HTTPException(status_code=404, detail="Universe not found")

    result = await db.execute(select(Character).where(Character.name == name, Character.universe_id == universe_id))
    char = result.scalars().first()

    if not char:
        # Create new character if they don't exist in this universe
        char = Character(
            name=name,
            universe_id=universe_id,
            is_pc=True,
            hp=10,
            max_hp=10,
            armor_class=10,
            speed=30
        )
        db.add(char)
        await db.commit()
        await db.refresh(char)

    return char
