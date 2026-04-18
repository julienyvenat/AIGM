with open("backend/src/world_builder/world_router.py", "r") as f:
    content = f.read()

content = content.replace(
    "from sqlmodel import select",
    "from sqlmodel import select\nfrom sqlalchemy.orm import selectinload"
)

content = content.replace(
    "result = await db.execute(select(Universe))",
    "result = await db.execute(select(Universe).options(selectinload(Universe.game_system)))"
)

with open("backend/src/world_builder/world_router.py", "w") as f:
    f.write(content)

with open("backend/src/main.py", "r") as f:
    main_content = f.read()

main_content = main_content.replace(
    "result = await db.execute(select(GameSession).where(GameSession.host_id == current_user.id))",
    "result = await db.execute(select(GameSession).where(GameSession.host_id == current_user.id).options(selectinload(GameSession.universe).selectinload(Universe.game_system)))"
)

new_endpoint = """
@app.get("/sessions/{session_id}/context")
async def get_session_context(session_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    import uuid
    from sqlmodel import select
    from sqlalchemy.orm import selectinload

    try:
        s_id = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    result = await db.execute(select(GameSession).where(GameSession.id == s_id).options(selectinload(GameSession.universe).selectinload(Universe.game_system)))
    session = result.scalars().first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session
"""

if "def get_session_context" not in main_content:
    main_content = main_content.replace(
        "@app.post(\"/sessions/{session_id}/join\")",
        new_endpoint + "\n@app.post(\"/sessions/{session_id}/join\")"
    )

with open("backend/src/main.py", "w") as f:
    f.write(main_content)
