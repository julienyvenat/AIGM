import re

with open('backend/src/main.py', 'r') as f:
    content = f.read()

# Make sure we don't duplicate
if 'from src.auth.deps import get_current_user' not in content:
    content = content.replace(
        'from src.engine.models import Character, WorldNPCTable',
        'from src.engine.models import Character, WorldNPCTable, User, GameSession, SessionParticipants\nfrom src.auth.deps import get_current_user'
    )

if '@app.post("/characters/")' not in content:
    new_routes = """
class CharacterCreate(BaseModel):
    name: str
    universe_id: str
    description: str | None = None

@app.post("/characters/")
async def create_character(char_data: CharacterCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    import uuid
    try:
        universe_id = uuid.UUID(char_data.universe_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid universe_id format")

    char = Character(
        name=char_data.name,
        universe_id=universe_id,
        user_id=current_user.id,
        is_pc=True,
        hp=10,
        max_hp=10,
        armor_class=10,
        speed=30
    )
    db.add(char)
    await db.commit()
    await db.refresh(char)
    return char

@app.get("/characters/")
async def get_characters(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    result = await db.execute(select(Character).where(Character.user_id == current_user.id))
    characters = result.scalars().all()
    # Find active sessions for each character if needed
    char_dicts = []
    for char in characters:
        char_dict = char.dict()
        # Look up active sessions via SessionParticipants
        query = select(SessionParticipants.session_id).where(SessionParticipants.character_id == char.id)
        session_res = await db.execute(query)
        session_id = session_res.scalars().first()
        char_dict["game_session_id"] = session_id
        char_dicts.append(char_dict)
    return char_dicts

class SessionCreate(BaseModel):
    universe_id: str

@app.post("/sessions/")
async def create_session(session_data: SessionCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    import uuid
    try:
        universe_id = uuid.UUID(session_data.universe_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid universe_id format")

    from src.engine.models import GameSessionStatus
    game_session = GameSession(
        universe_id=universe_id,
        host_id=current_user.id,
        status=GameSessionStatus.LOBBY
    )
    db.add(game_session)
    await db.commit()
    await db.refresh(game_session)
    return game_session

@app.get("/sessions/")
async def get_sessions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    # Get sessions where the user is host, or where their characters are participants
    from sqlmodel import or_, select
    from sqlalchemy.orm import selectinload

    # Simple approach for dashboard: just return all sessions the user hosts
    result = await db.execute(select(GameSession).where(GameSession.host_id == current_user.id))
    return result.scalars().all()

class JoinSessionRequest(BaseModel):
    character_id: str

@app.post("/sessions/{session_id}/join")
async def join_session(session_id: str, join_req: JoinSessionRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    import uuid
    try:
        s_id = uuid.UUID(session_id)
        c_id = uuid.UUID(join_req.character_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    # Verify character belongs to user
    char_result = await db.execute(select(Character).where(Character.id == c_id))
    char = char_result.scalars().first()

    if not char:
        raise HTTPException(status_code=404, detail="Character not found")

    if char.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this character")

    # Verify session exists
    session_result = await db.execute(select(GameSession).where(GameSession.id == s_id))
    game_session = session_result.scalars().first()

    if not game_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Check if already joined
    participant_query = select(SessionParticipants).where(
        SessionParticipants.session_id == s_id,
        SessionParticipants.character_id == c_id
    )
    participant_result = await db.execute(participant_query)

    if not participant_result.scalars().first():
        new_participant = SessionParticipants(session_id=s_id, character_id=c_id)
        db.add(new_participant)
        await db.commit()

    return {"status": "success", "message": "Joined session successfully"}

"""
    # Insert new routes after the image_generator functions imports
    content = content.replace(
        'from src.engine.models import Character, WorldNPCTable',
        'from src.engine.models import Character, WorldNPCTable\n' + new_routes
    )

    # We also need to add Depends to fastapi imports
    if 'Depends' not in content[:500]:
        content = content.replace('from fastapi import FastAPI', 'from fastapi import FastAPI, Depends, HTTPException')

    # We also need to add AsyncSession
    if 'AsyncSession' not in content[:500]:
        content = content.replace('from src.engine.database import init_db, get_session', 'from src.engine.database import init_db, get_session\nfrom sqlalchemy.ext.asyncio import AsyncSession')

with open('backend/src/main.py', 'w') as f:
    f.write(content)

print("Main patched")
