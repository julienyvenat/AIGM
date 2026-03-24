import re

with open("backend/src/agents/image_prompter.py", "r") as f:
    content = f.read()

# Update the signature and add the logic
content = content.replace(
    "async def generate_image_prompt(scene_description: str) -> str:",
    "async def generate_image_prompt(session: AsyncSession, player_id: str, scene_description: str) -> str:"
)

# Replace system_prompt block
old_block = """    system_prompt = (
        'Tu es un expert en Midjourney/DALL-E. Ta mission est de lire la description d\\'une scène de jeu '
        'de rôle et d\\'en extraire un prompt en anglais pour générer une image. Le prompt doit être concis, '
        'se concentrer sur le sujet, l\\'arrière-plan, l\\'éclairage. Ajoute toujours à la fin du prompt le style suivant : '
        '"digital painting, dark fantasy art style, highly detailed, masterpiece". Ne renvoie QUE le prompt, rien d\\'autre.'
    )"""

new_block = """    system_prompt = (
        'Tu es un expert en Midjourney/DALL-E. Ta mission est de lire la description d\\'une scène de jeu '
        'de rôle et d\\'en extraire un prompt en anglais pour générer une image. Le prompt doit être concis, '
        'se concentrer sur le sujet, l\\'arrière-plan, l\\'éclairage. Ajoute toujours à la fin du prompt le style suivant : '
        '"digital painting, dark fantasy art style, highly detailed, masterpiece". Ne renvoie QUE le prompt, rien d\\'autre.'
    )

    try:
        player_uuid = uuid.UUID(player_id)
        char = await session.get(Character, player_uuid)
        if char and char.reference_portrait_url:
            system_prompt += f"\\n\\nVoici le portrait de référence de notre héros : {char.reference_portrait_url}. Assure-toi que le personnage principal de la scène que tu décris lui ressemble trait pour trait (classe, visage, armure)."
    except Exception as e:
        print(f"Error fetching character portrait for player {player_id}: {e}")"""

content = content.replace(old_block, new_block)

with open("backend/src/agents/image_prompter.py", "w") as f:
    f.write(content)
