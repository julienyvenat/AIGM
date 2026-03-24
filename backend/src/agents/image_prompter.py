import os
import json
from pydantic import BaseModel
from openai import AsyncOpenAI
from google import genai
from google.genai import types

client = AsyncOpenAI() if os.environ.get("OPENAI_API_KEY") else None

gemini_client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY")) if os.environ.get("GOOGLE_API_KEY") else None

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")

class ImagePrompt(BaseModel):
    prompt: str

async def generate_image_prompt(scene_description: str) -> str:
    """
    Génère un prompt concis en anglais pour Midjourney/DALL-E 3 à partir d'une description de scène.
    """
    system_prompt = (
        'Tu es un expert en Midjourney/DALL-E. Ta mission est de lire la description d\'une scène de jeu '
        'de rôle et d\'en extraire un prompt en anglais pour générer une image. Le prompt doit être concis, '
        'se concentrer sur le sujet, l\'arrière-plan, l\'éclairage. Ajoute toujours à la fin du prompt le style suivant : '
        '"digital painting, dark fantasy art style, highly detailed, masterpiece". Ne renvoie QUE le prompt, rien d\'autre.'
    )

    if LLM_PROVIDER == "gemini":
        if not gemini_client:
            raise ValueError("GOOGLE_API_KEY is not set.")

        response = await gemini_client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=scene_description,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
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
