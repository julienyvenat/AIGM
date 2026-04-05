import re

with open("backend/src/engine/image_generator.py", "r") as f:
    content = f.read()

new_func = """
def generate_battlemap_prompt(description: str) -> str:
    \"\"\"
    Génère un prompt strict pour créer une battlemap tactique (top-down, pas de grille)
    à partir d'une description narrative.
    \"\"\"
    return (
        f"Top-down view (vue de dessus), orthographic projection, detailed battlemap for TTRPG, "
        f"clean environment, no grid marks. "
        f"Environment description: {description}. "
        f"Make sure it looks like a flat map viewed directly from above, suitable for placing tokens."
    )

async def generate_scene_image"""

content = content.replace("async def generate_scene_image", new_func)

with open("backend/src/engine/image_generator.py", "w") as f:
    f.write(content)
