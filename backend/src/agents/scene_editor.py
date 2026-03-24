import os
import json
import logging
from enum import Enum
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import google.generativeai as genai

logger = logging.getLogger(__name__)

class ImageDecision(str, Enum):
    GENERATE = "GENERATE"
    IGNORE = "IGNORE"

class SceneEditorResponse(BaseModel):
    decision: ImageDecision = Field(
        description="Décision finale de générer ou ignorer la scène visuelle."
    )

client = AsyncOpenAI() if os.environ.get("OPENAI_API_KEY") else None

if os.environ.get("GOOGLE_API_KEY"):
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

async def analyze_scene(text: str) -> SceneEditorResponse:
    """
    Analyse la description narrative du MJ pour décider si une image doit être générée.
    Retourne SceneEditorResponse avec 'decision' = GENERATE ou IGNORE.
    En cas d'erreur, retourne IGNORE par défaut.
    """
    system_prompt = """Tu es un monteur de scène pour un film. Ta mission est de décider si la description narrative du MJ nécessite une nouvelle image visuelle. Une image est nécessaire UNIQUEMENT s'il y a un changement de décor majeur, l'apparition d'un nouveau monstre/PNJ clé, ou le déclenchement d'une action de combat intense. Elle n'est PAS nécessaire pour des dialogues ou des descriptions d'expressions mineures. Ne renvoie QUE "GENERATE" ou "IGNORE" via un objet JSON."""

    try:
        if LLM_PROVIDER == "gemini":
            model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=system_prompt
            )
            response = await model.generate_content_async(
                text,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=SceneEditorResponse,
                )
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
