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

# Implémentation du stockage hybride
async def store_world_knowledge(knowledge: WorldKnowledge):
    from engine.database import get_session
    from engine.models import WorldNPCTable, WorldLocationTable, WorldFactionTable
    from memory.vector_db import add_to_memory

    # Insertion SQL
    async for session in get_session():
        for npc in knowledge.npc:
            db_npc = WorldNPCTable(
                nom=npc.nom,
                faction=npc.faction,
                description=npc.description,
                hp=npc.hp,
                armor_class=npc.armor_class
            )
            session.add(db_npc)
            # Vectorisation description NPC
            await add_to_memory(
                text=f"{npc.nom} : {npc.description}",
                memory_type="lore",
                metadata={"entity_type": "NPC", "name": npc.nom}
            )

        for loc in knowledge.location:
            db_loc = WorldLocationTable(
                nom=loc.nom,
                description=loc.description,
                points_interet=json.dumps(loc.points_interet)
            )
            session.add(db_loc)
            # Vectorisation description Location
            await add_to_memory(
                text=f"{loc.nom} : {loc.description}",
                memory_type="lore",
                metadata={"entity_type": "Location", "name": loc.nom}
            )

        for fac in knowledge.faction:
            db_fac = WorldFactionTable(
                nom=fac.nom,
                description=fac.description,
                relations_politiques=json.dumps(fac.relations_politiques)
            )
            session.add(db_fac)
            # Vectorisation description Faction
            await add_to_memory(
                text=f"{fac.nom} : {fac.description}",
                memory_type="lore",
                metadata={"entity_type": "Faction", "name": fac.nom}
            )

        await session.commit()
        break # Only one session needed

    # Vectorisation histoire globale
    if knowledge.histoire_globale:
        # Si c'est trop long, on peut le chunker ici aussi, mais add_to_memory
        # utilise les embedding models qui ont souvent une limite (ex: 8191 tokens pour text-embedding-3).
        # On va le chunker par précaution.
        histoire_chunks = chunk_text(knowledge.histoire_globale, max_tokens=2000)
        for i, chunk in enumerate(histoire_chunks):
             await add_to_memory(
                text=chunk,
                memory_type="lore",
                metadata={"entity_type": "GlobalHistory", "part": i+1}
            )
