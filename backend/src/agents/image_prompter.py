import os
import json
import uuid
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from engine.models import Character
from openai import AsyncOpenAI
import google.generativeai as genai

client = AsyncOpenAI() if os.environ.get("OPENAI_API_KEY") else None

if os.environ.get("GOOGLE_API_KEY"):
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

class ImagePrompt(BaseModel):
    prompt: str

async def generate_image_prompt(session: AsyncSession, player_id: str, scene_description: str) -> str:
    """
    Génère un prompt concis en anglais pour Midjourney/DALL-E 3 à partir d'une description de scène.
    """
    system_prompt = (
        'Tu es un expert en Midjourney/DALL-E. Ta mission est de lire la description d\'une scène de jeu '
        'de rôle et d\'en extraire un prompt en anglais pour générer une image. Le prompt doit être concis, '
        'se concentrer sur le sujet, l\'arrière-plan, l\'éclairage. Ajoute toujours à la fin du prompt le style suivant : '
        '"digital painting, dark fantasy art style, highly detailed, masterpiece". Ne renvoie QUE le prompt, rien d\'autre.'
    )

    try:
        player_uuid = uuid.UUID(player_id)
        char = await session.get(Character, player_uuid)
        if char and char.reference_portrait_url:
            system_prompt += f"\n\nVoici le portrait de référence de notre héros : {char.reference_portrait_url}. Assure-toi que le personnage principal de la scène que tu décris lui ressemble trait pour trait (classe, visage, armure)."
    except Exception as e:
        print(f"Error fetching character portrait for player {player_id}: {e}")

    if LLM_PROVIDER == "gemini":
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=system_prompt
        )
        response = await model.generate_content_async(
            scene_description,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ImagePrompt,
                temperature=0.7,
            )
        )
        parsed_dict = json.loads(response.text)
        return parsed_dict.get("prompt", "")
    else:
        if not client:
            raise ValueError("OPENAI_API_KEY is not set.")
        response = await client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": scene_description}
            ],
            response_format=ImagePrompt,
            temperature=0.7,
        )
        return response.choices[0].message.parsed.prompt
