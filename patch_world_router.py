with open("backend/src/world_builder/world_router.py", "r") as f:
    content = f.read()

new_endpoint = """
@router.get("/game-systems", response_model=List[GameSystem])
async def get_game_systems(db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(GameSystem))
    return result.scalars().all()
"""

if "def get_game_systems" not in content:
    content = content.replace("@router.get(\"/universes\", response_model=List[Universe])", new_endpoint + "\n@router.get(\"/universes\", response_model=List[Universe])")

    with open("backend/src/world_builder/world_router.py", "w") as f:
        f.write(content)
