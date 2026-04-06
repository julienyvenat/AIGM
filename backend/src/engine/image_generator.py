import asyncio
import aiofiles
import os
import logging
from openai import AsyncOpenAI
from google import genai
from google.genai import types
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI() if os.environ.get("OPENAI_API_KEY") else None

gemini_client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY")) if os.environ.get("GOOGLE_API_KEY") else None

IMAGE_PROVIDER = os.environ.get("IMAGE_PROVIDER", "openai").lower()

# Required for Imagen via google-genai API if available
async def _generate_imagen_image(prompt: str) -> str | None:
    try:
        if not gemini_client:
            raise ValueError("GOOGLE_API_KEY is not set.")


        # the google-genai library supports imagen using the models.generate_images method
        # wrapped in asyncio.to_thread to avoid blocking the event loop
        result = await asyncio.to_thread(
            gemini_client.models.generate_images,
            model='imagen-3.0-generate-002',
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1"
            )
        )

        if not result.generated_images:
            return None

        # Google returns bytes in the image object
        image_data = result.generated_images[0].image.image_bytes

        filename = f"{uuid.uuid4().hex}.png"

        # Ensure directory exists (Assuming frontend can serve this or we expose a route)
        await asyncio.to_thread(os.makedirs, "backend/images", exist_ok=True)
        filepath = os.path.join("backend/images", filename)

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(image_data)

        # Returning a relative URL assuming a static route could be setup,
        # but for now we just return the local path or a placeholder if static route isn't configured
        logger.info(f"Imagen generated successfully at {filepath}")
        return f"/images/{filename}"

    except Exception as e:
        logger.error(f"Erreur de génération d'image (Imagen): {e}")
        return None


def generate_battlemap_prompt(description: str) -> str:
    """
    Génère un prompt strict pour créer une battlemap tactique (top-down, pas de grille)
    à partir d'une description narrative.
    """
    return (
        f"Top-down view (vue de dessus), orthographic projection, detailed battlemap for TTRPG, "
        f"clean environment, no grid marks. "
        f"Environment description: {description}. "
        f"Make sure it looks like a flat map viewed directly from above, suitable for placing tokens."
    )

async def generate_scene_image(prompt: str) -> str | None:
    """
    Appelle l'API OpenAI (DALL-E 3) ou Google (Imagen) pour générer une image à partir d'un prompt.
    Renvoie l'URL de l'image générée en cas de succès, sinon None.
    """
    if IMAGE_PROVIDER == "google":
        return await _generate_imagen_image(prompt)
    else:
        # Default OpenAI
        try:
            if not client:
                raise ValueError("OPENAI_API_KEY is not set.")
            response = await client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            return response.data[0].url
        except Exception as e:
            logger.error(f"Erreur de génération d'image (OpenAI): {e}")
            return None

import httpx

async def download_image_locally(url: str, filename_prefix: str = "portrait") -> str:
    """
    Télécharge une image depuis une URL distante et l'enregistre localement.
    Retourne l'URL locale relative (ex: /images/portrait_xxx.png).
    """
    if not url.startswith("http"):
        return url # Already local or invalid

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            # Simple fallback for extension
            ext = "png"
            if "image/jpeg" in response.headers.get("content-type", ""):
                ext = "jpg"

            filename = f"{filename_prefix}_{uuid.uuid4().hex}.{ext}"
            await asyncio.to_thread(os.makedirs, "backend/images", exist_ok=True)
            filepath = os.path.join("backend/images", filename)

            async with aiofiles.open(filepath, "wb") as f:
                await f.write(response.content)

            logger.info(f"Image téléchargée avec succès: {filepath}")
            return f"/images/{filename}"
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement de l'image {url}: {e}")
        return url # Fallback to original URL on failure
