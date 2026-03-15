from pydantic import BaseModel
from openai import AsyncOpenAI

client = AsyncOpenAI()

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
