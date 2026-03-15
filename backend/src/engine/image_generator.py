import logging
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI()

async def generate_scene_image(prompt: str) -> str | None:
    """
    Appelle l'API OpenAI (DALL-E 3) pour générer une image à partir d'un prompt.
    Renvoie l'URL de l'image générée en cas de succès, sinon None.
    """
    try:
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        logger.error(f"Erreur de génération d'image: {e}")
        return None
