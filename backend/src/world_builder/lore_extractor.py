import sys
import asyncio
import os
import json
from typing import List
import tiktoken
from openai import AsyncOpenAI
from .schemas import WorldKnowledge, WorldNPC, WorldLocation, WorldFaction

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy_key"))

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))

def chunk_text(text: str, max_tokens: int = 3000, model: str = "gpt-4o-mini") -> List[str]:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    tokens = encoding.encode(text)
    chunks = []

    for i in range(0, len(tokens), max_tokens):
        chunk_tokens = tokens[i:i + max_tokens]
        chunk_str = encoding.decode(chunk_tokens)
        chunks.append(chunk_str)

    return chunks

async def extract_knowledge_from_chunk(chunk: str) -> WorldKnowledge:
    prompt = "Tu es un archiviste expert. Analyse ce texte et extrais toutes les entités (PNJ, Lieux, Factions) avec leurs statistiques si elles existent. Mets tout le reste (légendes, ambiance) dans histoire_globale."

    response = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": chunk}
        ],
        response_format=WorldKnowledge
    )

    return response.choices[0].message.parsed

async def extract_lore(text: str) -> WorldKnowledge:
    chunks = chunk_text(text, max_tokens=3000)

    extracted_knowledges = []
    for chunk in chunks:
        knowledge = await extract_knowledge_from_chunk(chunk)
        extracted_knowledges.append(knowledge)

    return merge_world_knowledges(extracted_knowledges)

def merge_world_knowledges(knowledges: List[WorldKnowledge]) -> WorldKnowledge:
    merged = WorldKnowledge()

    for k in knowledges:
        if k is None:
            continue
        merged.npc.extend(k.npc)
        merged.location.extend(k.location)
        merged.faction.extend(k.faction)

        if k.histoire_globale:
            if merged.histoire_globale:
                merged.histoire_globale += "\n\n" + k.histoire_globale
            else:
                merged.histoire_globale = k.histoire_globale

    return merged

# Implémentation du stockage hybride optimisé
async def store_world_knowledge(knowledge: WorldKnowledge):
    from src.engine.database import get_session
    from src.engine.models import WorldNPCTable, WorldLocationTable, WorldFactionTable
    from src.memory.vector_db import add_batch_to_memory

    sql_instances = []

    batch_texts = []
    batch_memory_types = []
    batch_metadatas = []

    # Prepare NPCs
    for npc in knowledge.npc:
        db_npc = WorldNPCTable(
            nom=npc.nom,
            faction=npc.faction,
            description=npc.description,
            hp=npc.hp,
            armor_class=npc.armor_class
        )
        sql_instances.append(db_npc)

        batch_texts.append(f"{npc.nom} : {npc.description}")
        batch_memory_types.append("lore")
        batch_metadatas.append({"entity_type": "NPC", "name": npc.nom})

    # Prepare Locations
    for loc in knowledge.location:
        db_loc = WorldLocationTable(
            nom=loc.nom,
            description=loc.description,
            points_interet=json.dumps(loc.points_interet)
        )
        sql_instances.append(db_loc)

        batch_texts.append(f"{loc.nom} : {loc.description}")
        batch_memory_types.append("lore")
        batch_metadatas.append({"entity_type": "Location", "name": loc.nom})

    # Prepare Factions
    for fac in knowledge.faction:
        db_fac = WorldFactionTable(
            nom=fac.nom,
            description=fac.description,
            relations_politiques=json.dumps(fac.relations_politiques)
        )
        sql_instances.append(db_fac)

        batch_texts.append(f"{fac.nom} : {fac.description}")
        batch_memory_types.append("lore")
        batch_metadatas.append({"entity_type": "Faction", "name": fac.nom})

    # Prepare Global History chunks
    if knowledge.histoire_globale:
        histoire_chunks = chunk_text(knowledge.histoire_globale, max_tokens=2000)
        for i, chunk in enumerate(histoire_chunks):
            batch_texts.append(chunk)
            batch_memory_types.append("lore")
            batch_metadatas.append({"entity_type": "GlobalHistory", "part": i+1})

    # Execute long running network requests (vector DB batch insertion) OUTSIDE the SQL transaction
    if batch_texts:
        await add_batch_to_memory(
            texts=batch_texts,
            memory_types=batch_memory_types,
            metadatas=batch_metadatas
        )

    # Execute SQL insertions efficiently with add_all inside a short-lived transaction
    if sql_instances:
        async for session in get_session():
            session.add_all(sql_instances)
            await session.commit()
            break # Only one session needed
