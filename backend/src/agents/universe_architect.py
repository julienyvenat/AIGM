import os
import json
import uuid
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from src.world_builder.schemas import WorldKnowledge
from src.engine.image_generator import generate_scene_image
from src.engine.models import Universe, WorldNPCTable, WorldLocationTable, WorldFactionTable, GameSystem

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_universe_from_prompt(prompt: str, game_system: GameSystem, db: AsyncSession) -> Universe:
    logging.info(f"Generating universe from prompt: {prompt}")

    # 1. Generate WorldKnowledge using structured outputs
    system_prompt = f"""
Tu es l'Architecte de l'Univers, un maître conteur et créateur de mondes.
Le monde doit respecter les contraintes du système de jeu suivant : {game_system.name}.
Résumé des règles et contraintes : {game_system.rules_summary}.
(Assure-toi que la magie, la technologie et les entités soient cohérentes avec ce système de jeu).

À partir de la description ou de la phrase fournie par l'utilisateur, crée un monde riche et cohérent.
Extrais les PNJ (nom, faction, description), les lieux (nom, description, points d'intérêt), et les factions (nom, description, relations politiques).
Génère une histoire globale captivante qui servira de contexte général au monde.
"""

    response = await client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        response_format=WorldKnowledge
    )

    world_knowledge: WorldKnowledge = response.choices[0].message.parsed

    # 2. Generate Universe Name
    name_prompt = f"Génère un nom court et épique (max 3-4 mots) pour cet univers :\n\n{world_knowledge.histoire_globale}"
    name_response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": name_prompt}],
        max_tokens=20
    )
    universe_name = name_response.choices[0].message.content.strip()

    # 3. Generate Image for the Universe
    image_prompt = f"Un paysage épique, concept art de l'univers : {universe_name}. Contexte: {prompt}. Magnifique, atmosphérique, chef-d'œuvre."
    # using generate_scene_image which creates image and returns url
    image_url = None
    try:
        image_url = await generate_scene_image(image_prompt)
    except Exception as e:
        logging.error(f"Failed to generate universe image: {e}")

    # 4. Save to Database
    universe = Universe(
        name=universe_name,
        description=world_knowledge.histoire_globale,
        image_url=image_url
    )
    db.add(universe)
    await db.flush() # get universe.id

    for npc_data in world_knowledge.npc:
        npc = WorldNPCTable(
            universe_id=universe.id,
            nom=npc_data.nom,
            faction=npc_data.faction,
            description=npc_data.description,
            hp=npc_data.hp,
            armor_class=npc_data.armor_class
        )
        db.add(npc)

    for loc_data in world_knowledge.location:
        loc = WorldLocationTable(
            universe_id=universe.id,
            nom=loc_data.nom,
            description=loc_data.description,
            points_interet=json.dumps(loc_data.points_interet)
        )
        db.add(loc)

    for fact_data in world_knowledge.faction:
        fact = WorldFactionTable(
            universe_id=universe.id,
            nom=fact_data.nom,
            description=fact_data.description,
            relations_politiques=json.dumps(fact_data.relations_politiques)
        )
        db.add(fact)

    await db.commit()
    await db.refresh(universe)

    return universe, world_knowledge
