import os
import random
import json
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from google import genai
from google.genai import types

from engine.models import Character

class ArbitratorLLMOutput(BaseModel):
    action_type: str = Field(description="Type of action (attack, spell, dodge, skill_check, etc.)")
    stat_used: str = Field(description="The stat used for this action: 'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', or 'charisma'.")
    difficulty_class: int = Field(description="The estimated Difficulty Class (DC) or Armor Class (AC) to beat, from 5 to 20.")
    consumed_resource_type: Optional[str] = Field(description="'spell_slot', 'class_resource', or null", default=None)
    consumed_resource_name: Optional[str] = Field(description="e.g. '3' for spell level 3, or 'ki_point'. null if none", default=None)

class ArbitratorResult(BaseModel):
    has_roll: bool
    roll_value: int
    modifier: int
    total: int
    success: bool
    hp_change: int
    consumed_resource_type: Optional[str] = None
    consumed_resource_name: Optional[str] = None

# Configuration OpenAI
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "")) if os.environ.get("OPENAI_API_KEY") else None
DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Configuration Gemini
gemini_client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY")) if os.environ.get("GOOGLE_API_KEY") else None

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

async def arbitrate_action(character: Character, intent_text: str) -> ArbitratorResult:
    """
    Use an LLM to determine the stat and difficulty, then securely roll the dice in Python.
    """
    system_prompt = f"""Tu es un arbitre strict de D&D 5e. Utilise tes connaissances internes du SRD officiel pour connaître les effets, les dégâts, les jets de sauvegarde et les portées des sorts et capacités. Tu ne peux valider l'action d'un joueur que s'il possède le sort dans sa liste et s'il lui reste des emplacements de sorts appropriés.

Le joueur tente l'action suivante : "{intent_text}"
Les stats du personnage sont :
Force: {character.strength}
Dextérité: {character.dexterity}
Constitution: {character.constitution}
Intelligence: {character.intelligence}
Sagesse: {character.wisdom}
Charisme: {character.charisma}

Inventaire magique et ressources :
Sorts connus: {character.known_spells}
Emplacements de sorts (Niveau: Quantité): {character.spell_slots}
Ressources de classe: {character.class_resources}

Analyse l'action et renvoie un objet JSON avec :
- action_type (string) : type d'action (attack, spell, etc.)
- stat_used (string) : l'une des 6 caractéristiques (strength, dexterity, constitution, intelligence, wisdom, charisma).
- difficulty_class (int) : une estimation de la difficulté (ex: 10 pour moyen, 15 pour difficile).
- consumed_resource_type (string|null) : "spell_slot", "class_resource", ou null si rien n'est consommé.
- consumed_resource_name (string|null) : le niveau de l'emplacement (ex: "3") ou le nom de la ressource (ex: "ki_point").
"""

    llm_output = None
    try:
        if LLM_PROVIDER == "gemini":
            if not gemini_client:
                 raise ValueError("GOOGLE_API_KEY is not set.")
            response = await gemini_client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=intent_text,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=ArbitratorLLMOutput,
                )
            )
            parsed_dict = json.loads(response.text)
            llm_output = ArbitratorLLMOutput(**parsed_dict)
        else:
            if not client:
                raise ValueError("OPENAI_API_KEY is not set.")
            # Use run_in_executor to not block event loop because OpenAI is sync here
            import asyncio
            loop = asyncio.get_event_loop()

            def make_call():
                return client.beta.chat.completions.parse(
                    model=DEFAULT_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": intent_text}
                    ],
                    response_format=ArbitratorLLMOutput,
                )

            response = await loop.run_in_executor(None, make_call)
            llm_output = response.choices[0].message.parsed

        if not llm_output:
            raise ValueError("LLM returned empty parsed output.")
    except Exception as e:
        print(f"Error in arbitrator LLM call: {e}")
        # Fallback
        llm_output = ArbitratorLLMOutput(
            action_type="unknown",
            stat_used="strength",
            difficulty_class=10
        )

    # 1. Get stat
    stat_val = getattr(character, llm_output.stat_used, 10)

    # 2. Calculate modifier
    modifier = (stat_val - 10) // 2

    # 3. Roll dice
    roll_value = random.randint(1, 20)
    total = roll_value + modifier

    # 4. Check success
    success = total >= llm_output.difficulty_class

    # 5. Determine hp_change (Simple asymmetrical logic for player damage)
    hp_change = 0
    if llm_output.action_type in ["dodge", "defend", "save"]:
        # Example: failed dodge means taking damage
        if not success:
            hp_change = -random.randint(1, 6) # D6 damage for failure

    # Note: If it's an attack, hp_change for player is 0, enemy damage handled by narrator.

    return ArbitratorResult(
        has_roll=True,
        roll_value=roll_value,
        modifier=modifier,
        total=total,
        success=success,
        hp_change=hp_change,
        consumed_resource_type=llm_output.consumed_resource_type,
        consumed_resource_name=llm_output.consumed_resource_name
    )
