import re

with open('backend/src/main.py', 'r') as f:
    content = f.read()

get_by_name_route = """
@app.get("/characters/by-name/{name}")
async def get_or_create_character_by_name(name: str):
    try:
        from engine.database import get_session
        from sqlmodel import select
        async for session in get_session():
            statement = select(Character).where(Character.name == name)
            result = await session.execute(statement)
            character = result.scalars().first()

            if not character:
                character = Character(
                    name=name,
                    is_pc=True,
                    hp=20,
                    max_hp=20,
                    armor_class=10,
                    speed=30
                )
                session.add(character)
                await session.commit()
                await session.refresh(character)

            return character
    except Exception as e:
        logger.error(f"Erreur get_or_create_character_by_name: {e}")
        return {"error": str(e)}

"""

# Insert the new route right before the existing /characters routes
match = re.search(r'class PortraitRequest\(BaseModel\):', content)
if match:
    new_content = content[:match.start()] + get_by_name_route + content[match.start():]
    with open('backend/src/main.py', 'w') as f:
        f.write(new_content)
    print("Patch applied.")
else:
    print("Could not find PortraitRequest")
