import os
import logging
from openai import AsyncOpenAI
import google.generativeai as genai
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI() if os.environ.get("OPENAI_API_KEY") else None

if os.environ.get("GOOGLE_API_KEY"):
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

IMAGE_PROVIDER = os.environ.get("IMAGE_PROVIDER", "openai").lower()

# Required for Imagen via google-generativeai API if available,
# although Vertex AI SDK is typically required for full Imagen 3 features
async def _generate_imagen_image(prompt: str) -> str | None:
    try:
        # Currently the official python sdk `google-generativeai` has limited
        # direct support for imagen outside of Vertex AI SDK, but we attempt
        # the standard approach if the library version supports it.
        # Fallback to local save since Google doesn't return hosted URLs like OpenAI.

        # NOTE: Imagen generation usually requires setting project IDs or using Vertex,
        # but the gemini api key alone sometimes enables it.

        # We will attempt the generate_images method if available
        # (It depends heavily on the specific module version)
        result = genai.ImageGenerationModel("imagen-3.0-generate-001").generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="1:1"
        )

        if not result.images:
            return None

        # We need to save the image to serve it, because Google returns bytes, not a URL
        image_data = result.images[0].image.image_bytes

        filename = f"{uuid.uuid4().hex}.png"

        # Ensure directory exists (Assuming frontend can serve this or we expose a route)
        os.makedirs("backend/images", exist_ok=True)
        filepath = os.path.join("backend/images", filename)

        with open(filepath, "wb") as f:
            f.write(image_data)

        # Returning a relative URL assuming a static route could be setup,
        # but for now we just return the local path or a placeholder if static route isn't configured
        logger.info(f"Imagen generated successfully at {filepath}")
        return f"/images/{filename}"

    except Exception as e:
        logger.error(f"Erreur de génération d'image (Imagen): {e}")
        return None

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
