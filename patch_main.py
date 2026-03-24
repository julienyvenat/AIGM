import re

with open("backend/src/main.py", "r") as f:
    content = f.read()

# Add necessary imports
imports = """from pydantic import BaseModel
from engine.image_generator import generate_scene_image, download_image_locally
from engine.models import Character"""

content = content.replace("from engine.image_generator import generate_scene_image", imports)

# Update background_image_generation signature and logic
old_func = "async def background_image_generation(description: str, manager: \"ConnectionManager\"):"
new_func = "async def background_image_generation(player_id: str, description: str, manager: \"ConnectionManager\"):"
content = content.replace(old_func, new_func)

old_logic = "prompt = await generate_image_prompt(description)"
new_logic = """async for session in get_session():
            prompt = await generate_image_prompt(session, player_id, description)
            break"""
content = content.replace(old_logic, new_logic)

# Update calls to background_image_generation
content = content.replace(
    "task = asyncio.create_task(background_image_generation(narrator_reply, manager))",
    "task = asyncio.create_task(background_image_generation(player_id, narrator_reply, manager))"
)

# Add Pydantic models for new routes
routes = """
class PortraitRequest(BaseModel):
    description: str

class ReferenceSetRequest(BaseModel):
    reference_portrait_url: str

@app.post("/characters/generate-portrait")
async def generate_portrait(request: PortraitRequest):
    \"\"\"Génère un portrait de personnage basé sur une description textuelle et le sauvegarde localement.\"\"\"
    try:
        # On utilise le même prompt generator mais orienté "portrait"
        # On pourrait aussi faire un prompt brut, pour faire simple on l'envoie direct à DALL-E / Imagen
        prompt = f"Character portrait, D&D style, fantasy RPG portrait. {request.description}. high quality, digital painting, detailed face"

        image_url = await generate_scene_image(prompt)
        if not image_url:
            return {"error": "Failed to generate image"}

        local_url = await download_image_locally(image_url, "portrait")
        return {"reference_portrait_url": local_url}

    except Exception as e:
        logger.error(f"Erreur generate_portrait: {e}")
        return {"error": str(e)}

@app.put("/characters/{character_id}/set-reference")
async def set_reference_portrait(character_id: str, request: ReferenceSetRequest):
    \"\"\"Met à jour l'URL du portrait de référence d'un personnage.\"\"\"
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from engine.database import get_session
        import uuid

        async for session in get_session():
            char = await session.get(Character, uuid.UUID(character_id))
            if not char:
                return {"error": f"Character {character_id} not found"}

            char.reference_portrait_url = request.reference_portrait_url
            session.add(char)
            await session.commit()
            return {"status": "success", "reference_portrait_url": char.reference_portrait_url}

    except Exception as e:
        logger.error(f"Erreur set_reference_portrait: {e}")
        return {"error": str(e)}

@app.websocket("/ws/{player_id}")
"""

content = content.replace("@app.websocket(\"/ws/{player_id}\")", routes)

with open("backend/src/main.py", "w") as f:
    f.write(content)
