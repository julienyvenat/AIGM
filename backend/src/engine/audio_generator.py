import asyncio
import aiofiles
import os
import logging
import uuid
from openai import AsyncOpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = AsyncOpenAI() if os.environ.get("OPENAI_API_KEY") else None

# tts-1 is OpenAI's cheapest/fastest TTS model ($0.015 / 1K characters as of
# writing, vs tts-1-hd at $0.030 / 1K characters for higher fidelity audio).
# Good enough for narration/NPC dialogue at the table; can be overridden via
# env var without a code change if Julien wants higher quality later.
TTS_MODEL = os.environ.get("TTS_MODEL", "tts-1")
TTS_VOICE = os.environ.get("TTS_VOICE", "alloy")


async def generate_speech_audio(text: str, filename_prefix: str = "narrator") -> str | None:
    """
    Appelle l'API OpenAI (Text-to-Speech) pour convertir un texte en audio et
    l'enregistre localement, en suivant le même pattern que
    `image_generator.py` (appel API asynchrone natif, écriture de fichier via
    aiofiles, retour d'une URL locale relative servie par StaticFiles).

    Renvoie l'URL locale relative de l'audio généré (ex: /audio/narrator_xxx.mp3)
    en cas de succès, sinon None.
    """
    if not text or not text.strip():
        return None

    try:
        if not client:
            raise ValueError("OPENAI_API_KEY is not set.")

        response = await client.audio.speech.create(
            model=TTS_MODEL,
            voice=TTS_VOICE,
            input=text,
            response_format="mp3",
        )

        audio_bytes = await response.aread()

        filename = f"{filename_prefix}_{uuid.uuid4().hex}.mp3"
        await asyncio.to_thread(os.makedirs, "backend/audio", exist_ok=True)
        filepath = os.path.join("backend/audio", filename)

        async with aiofiles.open(filepath, "wb") as f:
            await f.write(audio_bytes)

        logger.info(f"Audio TTS généré avec succès: {filepath}")
        return f"/audio/{filename}"

    except Exception as e:
        logger.error(f"Erreur de génération audio (OpenAI TTS): {e}")
        return None
