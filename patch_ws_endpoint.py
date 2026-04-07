import re

with open("backend/src/main.py", "r") as f:
    content = f.read()

# Make sure we import what we need
if "from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException, status, Query" not in content:
    content = content.replace(
        "from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect",
        "from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException, status, Query"
    )

if "from src.auth.utils import decode_access_token" not in content:
    content = content.replace(
        "from src.engine.image_generator import generate_image, determine_image_style",
        "from src.engine.image_generator import generate_image, determine_image_style\nfrom src.auth.utils import decode_access_token"
    )

if "from src.engine.models import GameSession, GameSessionStatus, SessionParticipants, User" not in content:
    content = content.replace(
        "from src.engine.models import Universe, Character, ChatMessage, IntentType",
        "from src.engine.models import Universe, Character, ChatMessage, IntentType, GameSession, GameSessionStatus, SessionParticipants, User"
    )

# Replace the WebSocket endpoint signature and add validation
ws_code = """@app.websocket("/ws/{session_id}/{character_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    character_id: str,
    token: str = Query(...)
):
    # Security Validation
    try:
        payload = decode_access_token(token)
        if not payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        username = payload.get("sub")
        if not username:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as e:
        logger.error(f"Erreur validation token WS: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # DB Validation
    try:
        async for session in get_session():
            import uuid

            # 1. User Validation
            stmt_user = select(User).where(User.username == username)
            res_user = await session.execute(stmt_user)
            user = res_user.scalars().first()
            if not user:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            # 2. Character Ownership
            stmt_char = select(Character).where(Character.id == uuid.UUID(character_id))
            res_char = await session.execute(stmt_char)
            char = res_char.scalars().first()
            if not char or char.user_id != user.id:
                logger.error(f"Utilisateur {username} n'est pas proprietaire du personnage {character_id}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            # 3. GameSession Existence & Status
            stmt_gs = select(GameSession).where(GameSession.id == uuid.UUID(session_id))
            res_gs = await session.execute(stmt_gs)
            gs = res_gs.scalars().first()
            if not gs or gs.status == GameSessionStatus.ENDED:
                logger.error(f"Session {session_id} invalide ou terminee")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            # 4. Session Participant
            stmt_part = select(SessionParticipants).where(
                SessionParticipants.session_id == uuid.UUID(session_id),
                SessionParticipants.character_id == uuid.UUID(character_id)
            )
            res_part = await session.execute(stmt_part)
            participant = res_part.scalars().first()
            if not participant:
                logger.error(f"Personnage {character_id} ne participe pas a la session {session_id}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

            break
    except Exception as e:
        logger.error(f"Erreur validation DB WS: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, session_id)"""

content = re.sub(
    r"@app.websocket\(\"/ws/\{player_id\}\"\)\nasync def websocket_endpoint\(websocket: WebSocket, player_id: str\):\n    await manager.connect\(websocket\)",
    ws_code,
    content
)

with open("backend/src/main.py", "w") as f:
    f.write(content)
