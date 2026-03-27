import os
import json
import logging
from enum import Enum
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class ImageDecision(str, Enum):
    GENERATE = "GENERATE"
    IGNORE = "IGNORE"

class SceneEditorResponse(BaseModel):
    decision: ImageDecision = Field(
        description="Décision finale de générer ou ignorer la scène visuelle."
    )

client = AsyncOpenAI() if os.environ.get("OPENAI_API_KEY") else None

# Configuration Gemini
gemini_client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY")) if os.environ.get("GOOGLE_API_KEY") else None

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

async def analyze_scene(text: str) -> SceneEditorResponse:
    """
    Analyse la description narrative du MJ pour décider si une image doit être générée.
    Retourne SceneEditorResponse avec 'decision' = GENERATE ou IGNORE.
    En cas d'erreur, retourne IGNORE par défaut.
    """
    system_prompt = """Tu es un monteur de scène pour un film. Ta mission est de décider si la description narrative du MJ nécessite une nouvelle image visuelle.
Tu dois choisir "GENERATE" dès qu'il y a un changement de pièce, la découverte d'un nouveau lieu (ex: ouvrir une porte, entrer dans une salle), l'apparition d'un nouveau monstre, ou la rencontre avec un PNJ important (ex: un roi, un boss). Ne choisis "IGNORE" que si les personnages discutent ou font de petites actions en restant exactement dans le même décor sans événement nouveau. Ne renvoie QUE "GENERATE" ou "IGNORE" via un objet JSON.

# EXEMPLES
Entrée : "Les lourdes portes en chêne cèdent sous votre poussée dans un grincement sinistre, révélant une immense salle du trône baignée par la lumière de la lune. Au fond, le Roi vous observe."
Sortie : {"decision": "GENERATE"}

Entrée : "L'aubergiste essuie une chope avec un chiffon sale et vous répond en soupirant : 'Les routes ne sont plus sûres mon ami...'"
Sortie : {"decision": "IGNORE"}
"""

    try:
        if LLM_PROVIDER == "gemini":
            if not gemini_client:
                raise ValueError("GOOGLE_API_KEY is not set.")
            
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=SceneEditorResponse,
            )
            response = await gemini_client.aio.models.generate_content(
                model=GEMINI_MODEL,
                contents=text,
                config=config,
            )
            parsed_dict = json.loads(response.text)
            return SceneEditorResponse(**parsed_dict)

        else: # Default to openai
            if not client:
                raise ValueError("OPENAI_API_KEY is not set.")
            response = await client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format=SceneEditorResponse,
            )

            parsed_response = response.choices[0].message.parsed
            if parsed_response is None:
                raise ValueError("L'IA n'a pas pu générer un objet JSON valide.")

            return parsed_response

    except Exception as e:
        logger.error(f"Error in scene_editor: {e}")
        return SceneEditorResponse(decision=ImageDecision.IGNORE)
