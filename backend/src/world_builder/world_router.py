from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from typing import List, Optional
import os
from openai import AsyncOpenAI
from pydantic import BaseModel

from engine.database import get_session
from engine.models import WorldNPCTable, WorldFactionTable
from memory.vector_db import get_relevant_context

router = APIRouter(prefix="/world", tags=["world"])

class ScenarioResponse(BaseModel):
    scenario: str

@router.get("/generate-scenario", response_model=ScenarioResponse)
async def generate_scenario(session = Depends(get_session)):
    try:
        # 1. Requête SQL pour lister 2-3 PNJ intéressants et 1-2 Factions
        npc_statement = select(WorldNPCTable).limit(3)
        npc_results = await session.execute(npc_statement)
        npcs = npc_results.scalars().all()

        faction_statement = select(WorldFactionTable).limit(2)
        faction_results = await session.execute(faction_statement)
        factions = faction_results.scalars().all()

        npc_context = "\n".join([f"PNJ: {npc.nom} - {npc.description}" for npc in npcs])
        faction_context = "\n".join([f"Faction: {f.nom} - {f.description}" for f in factions])

        # 2. Requête RAG pour avoir le ton du monde
        rag_query = "Conflits majeurs, mystères non résolus, guerres de factions et ambiance générale du monde"
        rag_context = await get_relevant_context(rag_query, limit=3, filter_type='lore')

        # 3. Générer l'intrigue
        prompt = f"""Tu es un Maître du Jeu expert. Génère une intrigue de scénario captivante basée sur ces éléments du monde:

        {rag_context}

        Implique ces PNJ :
        {npc_context}

        Et ces Factions :
        {faction_context}

        Le scénario doit comporter une accroche, un développement principal, et une fin ouverte.
        """

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy_key"))
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Tu es un Master du Jeu créatif."},
                {"role": "user", "content": prompt}
            ]
        )

        return ScenarioResponse(scenario=response.choices[0].message.content)

    except Exception as e:
        import logging
        logging.error(f"Erreur lors de la génération du scénario : {e}")
        raise HTTPException(status_code=500, detail=str(e))
