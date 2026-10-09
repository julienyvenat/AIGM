from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
from pydantic import BaseModel
import uuid

from src.engine.database import get_session
from src.engine.models import Universe, WorldNPCTable, WorldLocationTable, WorldFactionTable, Character, GameSystem
from src.agents.universe_architect import generate_universe_from_prompt
from src.memory.vector_db import add_to_memory, add_batch_to_memory

router = APIRouter()

class UniverseGenerateRequest(BaseModel):
    prompt: str
    game_system_id: uuid.UUID | None = None

@router.post("/world/generate-from-prompt")
async def generate_universe(req: UniverseGenerateRequest, db: AsyncSession = Depends(get_session)):
    # Fetch or default GameSystem
    if req.game_system_id:
        game_system = await db.get(GameSystem, req.game_system_id)
        if not game_system:
            raise HTTPException(status_code=404, detail="GameSystem not found")
    else:
        result = await db.execute(select(GameSystem).where(GameSystem.name == "SRD 5e Light"))
        game_system = result.scalars().first()
        if not game_system:
            raise HTTPException(status_code=500, detail="Default GameSystem 'SRD 5e Light' not found. Run the seed script.")

    # Create the universe and its entities
    universe, world_knowledge = await generate_universe_from_prompt(req.prompt, game_system, db)

    # Assign the GameSystem to the newly created Universe
    universe.game_system_id = game_system.id
    db.add(universe)
    await db.commit()
    await db.refresh(universe)

    # Save the global lore to ChromaDB with universe_id metadata
    await add_to_memory(
        text=world_knowledge.histoire_globale,
        memory_type="lore",
        metadata={"universe_id": str(universe.id), "entity_type": "global_history"}
    )

    # Save NPCs to ChromaDB
    if world_knowledge.npc:
        npc_texts = [f"{npc.nom} ({npc.faction or 'Sans faction'}): {npc.description}" for npc in world_knowledge.npc]
        npc_metadatas = [{"universe_id": str(universe.id), "entity_type": "NPC", "name": npc.nom} for npc in world_knowledge.npc]
        await add_batch_to_memory(
            texts=npc_texts,
            memory_types=["lore"] * len(npc_texts),
            metadatas=npc_metadatas
        )

    # Save Locations to ChromaDB
    if world_knowledge.location:
        loc_texts = [f"{loc.nom}: {loc.description}. Points d'intérêt: {', '.join(loc.points_interet)}" for loc in world_knowledge.location]
        loc_metadatas = [{"universe_id": str(universe.id), "entity_type": "Location", "name": loc.nom} for loc in world_knowledge.location]
        await add_batch_to_memory(
            texts=loc_texts,
            memory_types=["lore"] * len(loc_texts),
            metadatas=loc_metadatas
        )

    # Save Factions to ChromaDB
    if world_knowledge.faction:
        fact_texts = [f"{fact.nom}: {fact.description}. Relations: {', '.join(fact.relations_politiques)}" for fact in world_knowledge.faction]
        fact_metadatas = [{"universe_id": str(universe.id), "entity_type": "Faction", "name": fact.nom} for fact in world_knowledge.faction]
        await add_batch_to_memory(
            texts=fact_texts,
            memory_types=["lore"] * len(fact_texts),
            metadatas=fact_metadatas
        )

    return {"status": "success", "universe": universe}


@router.get("/game-systems", response_model=List[GameSystem])
async def get_game_systems(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(GameSystem))
    return result.scalars().all()

@router.get("/universes", response_model=List[Universe])
async def get_universes(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Universe).options(selectinload(Universe.game_system)))
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
    # Lightweight combat sheet (see WorldNPCTable) -- optional so existing
    # callers that only send nom/faction/description keep working.
    resistances: List[str] | None = None
    vulnerabilities: List[str] | None = None
    actions: List[Dict[str, Any]] | None = None

@router.put("/npcs/{npc_id}")
async def update_npc(npc_id: uuid.UUID, req: NPCPatch, db: AsyncSession = Depends(get_session)):
    npc = await db.get(WorldNPCTable, npc_id)
    if not npc:
        raise HTTPException(status_code=404, detail="NPC not found")
    npc.nom = req.nom
    npc.faction = req.faction
    npc.description = req.description
    if req.resistances is not None:
        npc.resistances = req.resistances
    if req.vulnerabilities is not None:
        npc.vulnerabilities = req.vulnerabilities
    if req.actions is not None:
        npc.actions = req.actions
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
