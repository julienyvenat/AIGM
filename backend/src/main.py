import json
import logging
import asyncio
from dotenv import load_dotenv

# Charger les variables d'environnement en premier
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from src.world_builder.world_router import router as world_router
from src.auth.router import auth_router
from src.config import get_cors_origins

from src.engine.database import init_db, get_session
from sqlalchemy.ext.asyncio import AsyncSession
from src.engine.models import ChatMessage
from sqlmodel import select, or_
from src.agents.router import analyze_player_intent, IntentType
from src.agents.arbitrator import arbitrate_action
from src.agents.narrator import generate_narrator_response
from src.memory.vector_db import get_relevant_context

from src.agents.scene_editor import analyze_scene, ImageDecision
from src.agents.image_prompter import generate_image_prompt
from pydantic import BaseModel
from src.engine.image_generator import generate_scene_image, download_image_locally, generate_battlemap_prompt
from src.engine.audio_generator import generate_speech_audio
from src.engine.models import Character, WorldNPCTable, User, GameSession, SessionParticipants, GameSystem, Universe, GMType
from src.engine.services.character_service import validate_character_stats, SchemaValidationError
from src.auth.deps import get_current_user, get_user_from_token



# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set global pour garder les références des tâches asynchrones (évite le GC)
background_tasks = set()

async def save_chat_message_background(player_id: str | None, sender: str, msg_type: str, content: str, category: str | None = None):
    """Sauvegarde un message de chat en arrière-plan."""
    try:
        async for session in get_session():
            new_msg = ChatMessage(
                player_id=player_id,
                sender=sender,
                type=msg_type,
                category=category,
                content=content
            )
            session.add(new_msg)
            await session.commit()
            break # On ne veut qu'une seule session
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du message en arrière-plan: {e}")

async def background_image_generation(player_id: str, description: str, manager: "ConnectionManager", session_id: str):
    try:
        # 1. Génération du prompt
        async for session in get_session():
            prompt = await generate_image_prompt(session, player_id, description)
            break
        logger.info(f"Image prompt généré: {prompt}")

        # 2. Génération de l'image
        image_url = await generate_scene_image(prompt)

        # 3. Broadcast si succès
        if image_url:
            logger.info(f"Image générée avec succès: {image_url}")
            await manager.broadcast_to_session({
                "type": "scene_image",
                "url": image_url
        }, session_id)
    except Exception as e:
        logger.error(f"Erreur dans background_image_generation: {e}")


async def background_tts_generation(text: str, manager: "ConnectionManager", session_id: str, source: str = "narrator"):
    """Génère l'audio (TTS) d'une réplique du Narrateur/PNJ en arrière-plan et
    diffuse son URL une fois prête, même pattern que background_image_generation
    ci-dessus. N'est appelée que si GameSession.voice_enabled est True (voir
    l'appelant) : aucun appel API ni coût si l'utilisateur n'a pas activé la voix."""
    try:
        audio_url = await generate_speech_audio(text, filename_prefix=source)

        if audio_url:
            logger.info(f"Audio TTS généré avec succès: {audio_url}")
            await manager.broadcast_to_session({
                "type": "audio_ready",
                "url": audio_url,
                "source": source,
            }, session_id)
    except Exception as e:
        logger.error(f"Erreur dans background_tts_generation: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    logger.info("Initialisation de la base de données...")
    await init_db()
    yield
    # Arrêt
    logger.info("Arrêt de l'application...")

app = FastAPI(lifespan=lifespan)
app.include_router(world_router)
app.include_router(auth_router)
import os
from fastapi.staticfiles import StaticFiles
os.makedirs("backend/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="backend/images"), name="images")
os.makedirs("backend/audio", exist_ok=True)
app.mount("/audio", StaticFiles(directory="backend/audio"), name="audio")

class CharacterCreate(BaseModel):
    name: str
    universe_id: str
    description: str | None = None
    stats: dict = {}

@app.post("/characters/")
async def create_character(char_data: CharacterCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    import uuid
    try:
        universe_id = uuid.UUID(char_data.universe_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid universe_id format")


    # Find the universe and game system to validate stats
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlmodel import select
    from src.engine.models import Universe, GameSystem
    from src.engine.services.character_service import validate_character_stats, SchemaValidationError

    universe = await db.get(Universe, universe_id)
    if not universe:
        raise HTTPException(status_code=400, detail="Universe not found")

    game_system = await db.get(GameSystem, universe.game_system_id)
    if not game_system:
        raise HTTPException(status_code=400, detail="GameSystem not found")

    # Validate character stats against game system schema
    if hasattr(char_data, 'stats'):
        try:
            validate_character_stats(char_data.stats, game_system.character_schema)
        except SchemaValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

    char = Character(
        name=char_data.name,
        universe_id=universe_id,
        user_id=current_user.id,
        is_pc=True,
        hp=10,
        max_hp=10,
        armor_class=10,
        speed=30,
        stats=char_data.stats
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
    # Who holds GM authority for this session: "AI" (default, current/
    # existing autonomous narrator+arbitrator behavior) or "HUMAN" (the
    # creator -- host_id -- becomes the human GM; see GameSession.gm_type).
    gm_type: str = "AI"

@app.post("/sessions/")
async def create_session(session_data: SessionCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    import uuid
    try:
        universe_id = uuid.UUID(session_data.universe_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid universe_id format")

    try:
        gm_type = GMType(session_data.gm_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid gm_type: must be 'AI' or 'HUMAN'")

    from src.engine.models import GameSessionStatus
    game_session = GameSession(
        universe_id=universe_id,
        host_id=current_user.id,
        status=GameSessionStatus.LOBBY,
        gm_type=gm_type,
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
    result = await db.execute(select(GameSession).where(GameSession.host_id == current_user.id).options(selectinload(GameSession.universe).selectinload(Universe.game_system)))
    return result.scalars().all()

class JoinSessionRequest(BaseModel):
    character_id: str


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

class VoiceToggleRequest(BaseModel):
    voice_enabled: bool

@app.put("/sessions/{session_id}/voice")
async def set_voice_enabled(session_id: str, request: VoiceToggleRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    """Active/désactive la narration vocale (TTS OpenAI) pour une session.
    Désactivé par défaut (coût par appel API) -- voir GameSession.voice_enabled.
    Seul l'hôte de la session peut la basculer, même convention que les autres
    routes de session (mêmes checks de propriété que /characters/{id}/set-reference)."""
    import uuid
    try:
        s_id = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    game_session = await db.get(GameSession, s_id)
    if not game_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if game_session.host_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You are not the host of this session")

    game_session.voice_enabled = request.voice_enabled
    db.add(game_session)
    await db.commit()
    await db.refresh(game_session)
    return {"status": "success", "voice_enabled": game_session.voice_enabled}
# Configuration CORS : liste d'origines autorisées pilotée par la variable
# d'environnement CORS_ORIGINS (une ou plusieurs origines séparées par des
# virgules, ex: "https://jdr.yvenat.eu"). Sans cette variable (dev local), on
# retombe sur une liste restreinte à localhost -- jamais de wildcard "*" en
# association avec allow_credentials=True (interdit par la spec CORS de
# toute façon, et surtout pas ce qu'on veut en production).
allowed_origins = get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)
        logger.info(f"Nouvelle connexion WebSocket établie pour la session {session_id}. Total session: {len(self.active_connections[session_id])}")

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
                logger.info(f"Connexion WebSocket fermée pour la session {session_id}. Reste: {len(self.active_connections[session_id])}")
            # Cleanup ghost websockets in memory
            if len(self.active_connections[session_id]) == 0:
                del self.active_connections[session_id]
                logger.info(f"Nettoyage de la session {session_id} (plus aucun joueur).")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Envoie un message JSON à un joueur spécifique."""
        await websocket.send_json(message)

    async def broadcast_to_session(self, message: dict, session_id: str):
        """Envoie un message JSON à tous les joueurs connectés d'une session spécifique."""
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi broadcast à la session {session_id}: {e}")

manager = ConnectionManager()



@app.get("/characters/by-name/{name}")
async def get_or_create_character_by_name(name: str):
    try:
        from src.engine.database import get_session
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

class PortraitRequest(BaseModel):
    description: str

class ReferenceSetRequest(BaseModel):
    reference_portrait_url: str

@app.post("/characters/generate-portrait")
async def generate_portrait(request: PortraitRequest, current_user: User = Depends(get_current_user)):
    """Génère un portrait de personnage basé sur une description textuelle et le sauvegarde localement."""
    try:
        # On utilise le même prompt generator mais orienté "portrait"
        # On pourrait aussi faire un prompt brut, pour faire simple on l'envoie direct à DALL-E / Imagen
        prompt = f"Character portrait, D&D style, fantasy RPG portrait. {request.description}. high quality, digital painting, detailed face"

        image_url = await generate_scene_image(prompt)
        if not image_url:
            return {"error": "Failed to generate image"}

        local_url = await download_image_locally(image_url, "portrait")
        return {"reference_portrait_url": local_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur generate_portrait: {e}")
        return {"error": str(e)}

@app.put("/characters/{character_id}/set-reference")
async def set_reference_portrait(character_id: str, request: ReferenceSetRequest, current_user: User = Depends(get_current_user)):
    """Met à jour l'URL du portrait de référence d'un personnage."""
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.engine.database import get_session
        import uuid

        async for session in get_session():
            char = await session.get(Character, uuid.UUID(character_id))
            if not char:
                return {"error": f"Character {character_id} not found"}

            if char.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Forbidden: You do not own this character")

            char.reference_portrait_url = request.reference_portrait_url
            session.add(char)
            await session.commit()
            return {"status": "success", "reference_portrait_url": char.reference_portrait_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur set_reference_portrait: {e}")
        return {"error": str(e)}

@app.websocket("/ws/{session_id}/{player_id}")

async def websocket_endpoint(websocket: WebSocket, session_id: str, player_id: str):
    import uuid

    # --- Auth: verify the JWT passed as a `token` query param (browsers
    # can't set custom WS headers, cf. AGENTS.md §7). Reject before
    # accepting the connection if it's missing/invalid, or if the
    # authenticated user isn't the owner of the `player_id` Character they
    # are trying to connect as (same ownership check as the
    # /sessions/{id}/join and /characters/{id}/set-reference HTTP routes).
    token = websocket.query_params.get("token")
    authorized_user = None
    if token:
        async for auth_session in get_session():
            authorized_user = await get_user_from_token(token, auth_session)
            break

    if authorized_user is None:
        logger.warning(
            f"Connexion WebSocket refusée (token manquant/invalide) pour player_id={player_id}, session={session_id}."
        )
        await websocket.close(code=1008)
        return

    try:
        character_uuid = uuid.UUID(player_id)
    except ValueError:
        character_uuid = None

    owns_character = False
    if character_uuid is not None:
        async for auth_session in get_session():
            char_result = await auth_session.execute(select(Character).where(Character.id == character_uuid))
            character = char_result.scalars().first()
            owns_character = character is not None and character.user_id == authorized_user.id
            break

    if not owns_character:
        logger.warning(
            f"Connexion WebSocket refusée (utilisateur {authorized_user.id} n'est pas propriétaire du personnage {player_id})."
        )
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, session_id)

    # Load and send chat history
    try:
        async for session in get_session():
            statement = select(ChatMessage).where(
                or_(ChatMessage.player_id == player_id, ChatMessage.player_id == None)
            ).order_by(ChatMessage.timestamp)
            results = await session.execute(statement)
            history_msgs = results.scalars().all()

            history_payload = []
            for msg in history_msgs:
                history_payload.append({
                    "id": str(msg.id),
                    "sender": msg.sender,
                    "type": msg.type,
                    "category": msg.category,
                    "message": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                })

            if history_payload:
                await manager.send_personal_message(
                    {"type": "history", "messages": history_payload},
                    websocket
                )

            # Send initial battle state if applicable
            # (game_mode / battlemap state live on the GameSession, not the Character)
            async for session in get_session():
                import uuid
                try:
                    game_session_uuid = uuid.UUID(session_id)
                except ValueError:
                    game_session_uuid = None
                game_session = await session.get(GameSession, game_session_uuid) if game_session_uuid else None
                if game_session and game_session.game_mode == "BATTLE" and game_session.current_battlemap_url:
                    await manager.send_personal_message(
                        {"type": "battlemap_update", "url": game_session.current_battlemap_url},
                        websocket
                    )

                    # Also send combat state
                    from src.agents.narrator import get_combat_state
                    combat_state = await get_combat_state(session, game_session.universe_id)
                    await manager.send_personal_message(
                        {
                            "type": "combat_state",
                            "entities": combat_state,
                            "grid_width": game_session.grid_width,
                            "grid_height": game_session.grid_height,
                        },
                        websocket
                    )
                break
    except Exception as e:
        logger.error(f"Erreur lors du chargement de l'historique pour {player_id}: {e}")

    try:
        while True:
            # Réception du message sous forme de texte brut
            data = await websocket.receive_text()

            # 1. Parsing du JSON
            try:
                payload = json.loads(data)
            except json.JSONDecodeError as e:
                logger.warning(f"Message JSON invalide de {player_id}: {e}")
                await manager.send_personal_message(
                    {"type": "error", "message": "Format JSON invalide."},
                    websocket
                )
                continue

            # --- GM authority (Phase D) ---
            # Looked up once per message and reused below to gate GM-only
            # actions (/battle, /endbattle, the gm_consult_*/gm_generate_scene
            # UI_ACTIONs) and to branch the narration pipeline just before
            # intent analysis. Computing it here -- instead of threading a
            # conditional through every existing line below -- keeps the
            # AI-GM code path (game_session_gm_type == GMType.AI, the
            # default) completely untouched: `is_session_gm` is always False
            # for it, so every gate below is a no-op and every branch below
            # falls through to the pre-existing behavior unchanged.
            import uuid as _uuid_gm_check
            game_session_gm_type = GMType.AI
            is_session_gm = False
            async for session in get_session():
                try:
                    _gs_for_gm_check = await session.get(GameSession, _uuid_gm_check.UUID(session_id))
                except ValueError:
                    _gs_for_gm_check = None
                if _gs_for_gm_check:
                    game_session_gm_type = _gs_for_gm_check.gm_type
                    is_session_gm = (
                        game_session_gm_type == GMType.HUMAN
                        and _gs_for_gm_check.host_id == authorized_user.id
                    )
                break

            # Check for UI Actions bypassing the LLM
            if payload.get("type") == "UI_ACTION":
                action = payload.get("action")

                if action in ("gm_consult_narrator", "gm_consult_arbitrator", "gm_generate_scene"):
                    # --- Human-GM on-demand AI consultation (Phase D) ---
                    # These give a human GM the same underlying AI
                    # capabilities the AI-GM path uses autonomously
                    # (narrator prose, arbitrator dice/outcome resolution,
                    # scene-image generation), but as an advisory tool the
                    # GM explicitly calls -- never auto-broadcast as the
                    # authoritative outcome. Only the session's human GM may
                    # use them (same "only GM" authorization as /battle
                    # below), and only in a HUMAN-GM session (they'd be
                    # redundant in an AI-GM one, which already narrates
                    # autonomously).
                    if not is_session_gm:
                        await manager.send_personal_message(
                            {"type": "error", "message": "Seul le MJ humain de cette session peut faire ça."},
                            websocket
                        )
                        continue

                    if action == "gm_consult_narrator":
                        situation_text = payload.get("text", "")
                        async for session in get_session():
                            game_session = await session.get(GameSession, _uuid_gm_check.UUID(session_id))
                            game_mode = game_session.game_mode if game_session else "NARRATIVE"
                            try:
                                suggestion = await generate_narrator_response(
                                    session, player_id, situation_text, game_mode=game_mode
                                )
                            except Exception as e:
                                logger.error(f"Erreur gm_consult_narrator: {e}")
                                suggestion = None
                            break

                        if suggestion is not None:
                            # Personal message only -- advisory, not broadcast.
                            await manager.send_personal_message(
                                {"type": "gm_advisory", "advisory_type": "narrator", "message": suggestion},
                                websocket
                            )
                        else:
                            await manager.send_personal_message(
                                {"type": "error", "message": "Le narrateur n'a pas pu générer de suggestion."},
                                websocket
                            )
                        continue

                    if action == "gm_consult_arbitrator":
                        # Advisory arbitration for ANY entity in the universe
                        # (the acting Character, or a WorldNPCTable -- e.g.
                        # to resolve an NPC's combat turn), by entity_id.
                        # Returns the ArbitratorResult as-is: it is never
                        # applied to HP/resources automatically, unlike the
                        # AI-GM ACTION-intent pipeline in main.py below --
                        # the human GM decides what to actually apply.
                        entity_id_str = payload.get("entity_id")
                        action_text = payload.get("text", "")
                        arb_result = None
                        arb_error = None
                        async for session in get_session():
                            game_session = await session.get(GameSession, _uuid_gm_check.UUID(session_id))
                            entity = None
                            try:
                                entity_uuid = _uuid_gm_check.UUID(entity_id_str) if entity_id_str else None
                            except ValueError:
                                entity_uuid = None
                            if entity_uuid and game_session:
                                char_res = await session.execute(select(Character).where(Character.id == entity_uuid))
                                entity = char_res.scalars().first()
                                if not entity:
                                    npc_res = await session.execute(select(WorldNPCTable).where(WorldNPCTable.id == entity_uuid))
                                    entity = npc_res.scalars().first()

                            if not entity or not game_session or entity.universe_id != game_session.universe_id:
                                arb_error = "Entité introuvable dans cette session."
                                break

                            uni = await session.get(Universe, game_session.universe_id)
                            game_system = await session.get(GameSystem, uni.game_system_id) if uni and uni.game_system_id else None
                            if not game_system:
                                gs_result = await session.execute(select(GameSystem).where(GameSystem.name == "SRD 5e Light"))
                                game_system = gs_result.scalars().first()
                            if not game_system:
                                arb_error = "Aucun système de jeu configuré pour cet univers."
                                break

                            arb_result = await arbitrate_action(entity, game_system, action_text)
                            break

                        if arb_error:
                            await manager.send_personal_message({"type": "error", "message": arb_error}, websocket)
                        else:
                            await manager.send_personal_message(
                                {
                                    "type": "gm_advisory",
                                    "advisory_type": "arbitrator",
                                    "result": {
                                        "action_type": arb_result.action_type,
                                        "narrative": arb_result.narrative,
                                        "success": arb_result.success,
                                        "hp_change": arb_result.hp_change,
                                        "consumed_resource_type": arb_result.consumed_resource_type,
                                        "consumed_resource_name": arb_result.consumed_resource_name,
                                    },
                                },
                                websocket
                            )
                        continue

                    if action == "gm_generate_scene":
                        # Manually trigger the same scene-image pipeline the
                        # AI-GM path fires automatically off a narrator
                        # reply (background_image_generation) -- broadcasts
                        # `scene_image` to everyone once ready, same as
                        # before, but here the human GM is the one deciding
                        # a scene is worth illustrating.
                        description = payload.get("description", "")
                        task = asyncio.create_task(background_image_generation(player_id, description, manager, session_id))
                        background_tasks.add(task)
                        task.add_done_callback(background_tasks.discard)
                        continue

                if action == "move_entity":
                    # Manual token placement on the Battlemap (drag & drop of a
                    # PC or NPC token to a new cell). Bypasses the LLM entirely,
                    # same as the other UI_ACTIONs below, but moves any entity
                    # in the caller's universe rather than the caller's own
                    # inventory, so it is handled separately.
                    import uuid
                    from src.engine.tools import set_entity_position

                    entity_id_str = payload.get("entity_id")
                    target_x = payload.get("x")
                    target_y = payload.get("y")

                    if entity_id_str is not None and target_x is not None and target_y is not None:
                        async for session in get_session():
                            try:
                                mover_stmt = select(Character).where(Character.id == uuid.UUID(player_id))
                                mover_res = await session.execute(mover_stmt)
                                mover = mover_res.scalars().first()

                                game_session_uuid = uuid.UUID(session_id)
                                game_session = await session.get(GameSession, game_session_uuid)

                                if not mover or not game_session or mover.universe_id != game_session.universe_id:
                                    await manager.send_personal_message(
                                        {"type": "error", "message": "Action non autorisée."}, websocket
                                    )
                                    break

                                result = await set_entity_position(
                                    session,
                                    uuid.UUID(entity_id_str),
                                    game_session.universe_id,
                                    target_x,
                                    target_y,
                                    grid_width=game_session.grid_width,
                                    grid_height=game_session.grid_height,
                                )

                                if result.get("status") == "success":
                                    from src.agents.narrator import get_combat_state
                                    c_state = await get_combat_state(session, game_session.universe_id)
                                    await manager.broadcast_to_session({
                                        "type": "combat_state",
                                        "entities": c_state,
                                        "grid_width": game_session.grid_width,
                                        "grid_height": game_session.grid_height,
                                    }, session_id)
                                else:
                                    await manager.send_personal_message(
                                        {"type": "error", "message": result.get("message", "Impossible de déplacer le pion.")},
                                        websocket
                                    )
                            except Exception as e:
                                logger.error(f"Error processing move_entity UI_ACTION: {e}")
                                await manager.send_personal_message(
                                    {"type": "error", "message": "Erreur lors du déplacement du pion."},
                                    websocket
                                )
                            break
                    continue

                item_id_str = payload.get("item_id")

                if action and item_id_str:
                    import uuid
                    from src.engine.models import InventorySlot, Item
                    from src.engine.tools import roll_dice

                    async for session in get_session():
                        try:
                            # Verify character
                            stmt_char = select(Character).where(Character.id == uuid.UUID(player_id))
                            res_char = await session.execute(stmt_char)
                            char = res_char.scalars().first()

                            if char:
                                # Find inventory slot
                                stmt_slot = select(InventorySlot).where(
                                    InventorySlot.id == uuid.UUID(item_id_str),
                                    InventorySlot.character_id == char.id
                                )
                                res_slot = await session.execute(stmt_slot)
                                slot = res_slot.scalars().first()

                                if slot:
                                    # Fetch item details
                                    stmt_item = select(Item).where(Item.id == slot.item_id)
                                    res_item = await session.execute(stmt_item)
                                    item = res_item.scalars().first()

                                    system_message = ""
                                    needs_stats_update = False

                                    if action == "equip":
                                        if item.item_type in ["WEAPON", "ARMOR"]:
                                            slot.is_equipped = not slot.is_equipped
                                            session.add(slot)
                                            state = "équiper" if slot.is_equipped else "déséquiper"
                                            system_message = f"{char.name} vient de {state} : {item.name}."
                                            needs_stats_update = True

                                    elif action == "use":
                                        if item.item_type == "CONSUMABLE" and slot.quantity > 0:
                                            slot.quantity -= 1
                                            effect_msg = ""
                                            if item.attributes and "healing" in item.attributes:
                                                healing_roll = roll_dice(item.attributes["healing"])
                                                old_hp = char.hp
                                                char.hp = min(char.max_hp, char.hp + healing_roll)
                                                healed = char.hp - old_hp
                                                effect_msg = f" et regagne {healed} PV"
                                                session.add(char)

                                            if slot.quantity <= 0:
                                                await session.delete(slot)
                                            else:
                                                session.add(slot)

                                            system_message = f"{char.name} utilise {item.name}{effect_msg}."
                                            needs_stats_update = True

                                    if needs_stats_update:
                                        await session.commit()

                                        # Broadcast system message
                                        await manager.broadcast_to_session({
                                            "type": "system",
                                            "category": "SYSTEM",
                                            "message": system_message
                                        }, session_id)

                                        # Refresh and send STATS_UPDATE
                                        await session.refresh(char)
                                        from sqlalchemy.orm import selectinload
                                        st_refresh = select(Character).options(selectinload(Character.inventory).selectinload(InventorySlot.item)).where(Character.id == char.id)
                                        res_refresh = await session.execute(st_refresh)
                                        char_refreshed = res_refresh.scalars().first()

                                        known_spells_parsed = []
                                        spell_slots_parsed = {}
                                        class_resources_parsed = {}
                                        try:
                                            known_spells_parsed = json.loads(char_refreshed.known_spells)
                                            spell_slots_parsed = json.loads(char_refreshed.spell_slots)
                                            class_resources_parsed = json.loads(char_refreshed.class_resources)
                                        except Exception:
                                            pass

                                        inv_list = []
                                        if char_refreshed and char_refreshed.inventory:
                                            for s in char_refreshed.inventory:
                                                inv_list.append({
                                                    "id": str(s.id),
                                                    "quantity": s.quantity,
                                                    "is_equipped": s.is_equipped,
                                                    "item": {
                                                        "id": str(s.item.id),
                                                        "name": s.item.name,
                                                        "description": s.item.description,
                                                        "item_type": s.item.item_type.value,
                                                        "attributes": s.item.attributes
                                                    }
                                                })

                                        await manager.send_personal_message({
                                            "type": "stats_update",
                                            "character": {
                                                "id": str(char_refreshed.id),
                                                "name": char_refreshed.name,
                                                "hp": char_refreshed.hp,
                                                "max_hp": char_refreshed.max_hp,
                                                "armor_class": char_refreshed.armor_class,
                                                "speed": char_refreshed.speed,
                                                "reference_portrait_url": char_refreshed.reference_portrait_url,
                                                "strength": char_refreshed.strength,
                                                "dexterity": char_refreshed.dexterity,
                                                "constitution": char_refreshed.constitution,
                                                "intelligence": char_refreshed.intelligence,
                                                "wisdom": char_refreshed.wisdom,
                                                "charisma": char_refreshed.charisma,
                                                "level": char_refreshed.level,
                                                "experience": char_refreshed.experience,
                                                "known_spells": known_spells_parsed,
                                                "spell_slots": spell_slots_parsed,
                                                "class_resources": class_resources_parsed,
                                                "inventory": inv_list
                                            }
                                        }, websocket)

                        except Exception as e:
                            logger.error(f"Error processing UI_ACTION: {e}")
                        break
                continue

            player_text = payload.get("text")
            if not player_text:
                await manager.send_personal_message(
                    {"type": "error", "message": "Le champ 'text' est manquant ou vide."},
                    websocket
                )
                continue


            # Sanitize player_id and player_text to prevent log injection
            sanitized_player_id = str(player_id).replace('\n', '\\n').replace('\r', '\\r')
            sanitized_player_text = str(player_text).replace('\n', '\\n').replace('\r', '\\r')
            logger.info(f"[{sanitized_player_id}] Dit: {sanitized_player_text}")

            # Save player message (background). In a HUMAN-GM session, the
            # GM's own chat message IS the table's authoritative narration
            # (see the pre-intent-analysis branch below) -- persist it with
            # a distinguishing sender/type/category so a reconnect's chat
            # history replay renders it the same way live clients see it.
            if game_session_gm_type == GMType.HUMAN and is_session_gm:
                task = asyncio.create_task(save_chat_message_background(player_id, "gm", "narrator", player_text, "GM"))
            else:
                task = asyncio.create_task(save_chat_message_background(player_id, "user", "chat", player_text))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

            if player_text.strip() == "/battle":
                if game_session_gm_type == GMType.HUMAN and not is_session_gm:
                    await manager.send_personal_message(
                        {"type": "error", "message": "Seul le MJ peut déclencher le mode combat dans une session à MJ humain."},
                        websocket
                    )
                    continue
                import uuid
                async for session in get_session():
                    statement = select(Character).where(Character.id == uuid.UUID(player_id))
                    result = await session.execute(statement)
                    char = result.scalars().first()
                    # game_mode / battlemap state live on the GameSession, not the
                    # Character (see the on-connect handler above) -- Character has
                    # no `game_mode`/`battlemap_image_url` field.
                    game_session = await session.get(GameSession, uuid.UUID(session_id))
                    if char and game_session:
                        game_session.game_mode = "BATTLE"
                        char.x = 7
                        char.y = 2

                        # Set active enemies (just an example, fetching some NPCs and setting them to combat)
                        npc_statement = select(WorldNPCTable).where(WorldNPCTable.universe_id == char.universe_id).limit(3)
                        npc_result = await session.execute(npc_statement)
                        npcs = npc_result.scalars().all()
                        for idx, npc in enumerate(npcs):
                            npc.is_in_combat = True
                            npc.x = 5 + idx * 2
                            npc.y = 10
                            session.add(npc)

                        # Variable grid size: derive it from the actual spread of
                        # entities placed on the map rather than a hardcoded 15x15,
                        # with generous padding so tokens aren't hugging the edge.
                        placed_x = [char.x] + [5 + idx * 2 for idx in range(len(npcs))]
                        placed_y = [char.y] + [10 for _ in npcs]
                        game_session.grid_width = max(15, min(40, max(placed_x) + 4))
                        game_session.grid_height = max(15, min(40, max(placed_y) + 4))

                        session.add(char)
                        session.add(game_session)
                        await session.commit()

                        sys_msg = "The player just initiated combat. Describe the current environment and the enemies present in one short paragraph."
                        narrator_reply = await generate_narrator_response(session, player_id, sys_msg, game_mode="BATTLE")

                        await manager.broadcast_to_session({
                            "type": "narrator",
                            "category": "SYSTEM",
                            "message": narrator_reply
        }, session_id)

                        # Trigger battlemap generation
                        async def generate_and_update_battlemap(desc, gs_id):
                            bm_prompt = generate_battlemap_prompt(desc)
                            img_url = await generate_scene_image(bm_prompt)
                            if img_url:
                                local_url = await download_image_locally(img_url, "battlemap")
                                async for s in get_session():
                                    gs = await s.get(GameSession, gs_id)
                                    if gs:
                                        gs.current_battlemap_url = local_url
                                        s.add(gs)
                                        await s.commit()
                                        await manager.broadcast_to_session({
                                            "type": "battlemap_update",
                                            "url": local_url
        }, session_id)
                                    break

                        task = asyncio.create_task(generate_and_update_battlemap(narrator_reply, game_session.id))
                        background_tasks.add(task)
                        task.add_done_callback(background_tasks.discard)

                        from src.agents.narrator import get_combat_state
                        c_state = await get_combat_state(session, char.universe_id)
                        await manager.broadcast_to_session({
                            "type": "combat_state",
                            "entities": c_state,
                            "grid_width": game_session.grid_width,
                            "grid_height": game_session.grid_height,
        }, session_id)
                    break
                continue

            if player_text.strip() == "/endbattle":
                if game_session_gm_type == GMType.HUMAN and not is_session_gm:
                    await manager.send_personal_message(
                        {"type": "error", "message": "Seul le MJ peut mettre fin au combat dans une session à MJ humain."},
                        websocket
                    )
                    continue
                import uuid
                async for session in get_session():
                    statement = select(Character).where(Character.id == uuid.UUID(player_id))
                    result = await session.execute(statement)
                    char = result.scalars().first()
                    game_session = await session.get(GameSession, uuid.UUID(session_id))
                    if char and game_session:
                        game_session.game_mode = "NARRATIVE"
                        game_session.current_battlemap_url = None
                        game_session.grid_width = 15
                        game_session.grid_height = 15

                        npc_statement = select(WorldNPCTable).where(WorldNPCTable.universe_id == char.universe_id).where(WorldNPCTable.is_in_combat == True)
                        npc_result = await session.execute(npc_statement)
                        npcs = npc_result.scalars().all()
                        for npc in npcs:
                            npc.is_in_combat = False
                            session.add(npc)

                        session.add(game_session)
                        await session.commit()

                        await manager.broadcast_to_session({
                            "type": "system",
                            "message": "Le combat est terminé."
        }, session_id)
                        await manager.broadcast_to_session({
                            "type": "battlemap_update",
                            "url": None
        }, session_id)
                        await manager.broadcast_to_session({
                            "type": "combat_state",
                            "entities": [],
                            "grid_width": game_session.grid_width,
                            "grid_height": game_session.grid_height,
        }, session_id)
                    break
                continue

            # --- HUMAN-GM narration branch (Phase D) ---
            # In a HUMAN-GM session, the AI never autonomously narrates or
            # arbitrates outcomes (the human GM does, using their own chat
            # messages as authoritative narration and the gm_consult_*
            # UI_ACTIONs above as an on-demand advisory tool). This branches
            # BEFORE intent analysis so the entire ROLEPLAY/ACTION/SYSTEM
            # pipeline below -- the AI-GM path -- is completely untouched
            # and still runs exactly as before for game_session_gm_type ==
            # GMType.AI (the default).
            if game_session_gm_type == GMType.HUMAN:
                if is_session_gm:
                    # The GM's own message is the table's official outcome:
                    # broadcast with a distinguishing marker instead of
                    # running it through the AI pipeline.
                    await manager.broadcast_to_session({
                        "type": "narrator",
                        "category": "GM",
                        "message": player_text,
                        "role": "gm",
                    }, session_id)
                else:
                    # Regular player chat: still broadcast to everyone
                    # (including the GM) so the table can see what was
                    # said/typed, but no AI narration/arbitration follows --
                    # the human GM decides what happens next.
                    await manager.broadcast_to_session({
                        "type": "chat",
                        "category": "PLAYER",
                        "message": player_text,
                        "role": "player",
                        "player_id": player_id,
                    }, session_id)
                continue

            # 2. Analyse de l'intention
            intent = analyze_player_intent(player_text)
            logger.info(f"[{player_id}] Intention détectée: {intent.intent.value} ({intent.action_type})")

            # 3. Aiguillage
            if intent.intent == IntentType.IGNORE:
                # On ne fait rien, on continue la boucle
                continue

            elif intent.intent in (IntentType.ROLEPLAY, IntentType.ACTION):
                # --- ARBITRATION BLOCK ---
                arbitration_context = ""
                if intent.intent == IntentType.ACTION:
                    import uuid
                    async for session in get_session():
                        # Try to find the character for this player
                        statement = select(Character).where(Character.id == uuid.UUID(player_id))
                        result = await session.execute(statement)
                        char = result.scalars().first()

                        if char:
                            # Fetch the universe and its game_system
                            uni = await session.get(Universe, char.universe_id)
                            if not uni or not uni.game_system_id:
                                # Fallback to default
                                gs_result = await session.execute(select(GameSystem).where(GameSystem.name == "SRD 5e Light"))
                                game_system = gs_result.scalars().first()
                            else:
                                game_system = await session.get(GameSystem, uni.game_system_id)

                            # Run arbitration
                            arbitration_res = await arbitrate_action(char, game_system, player_text)

                            # Deduct resource if consumed
                            needs_update = False
                            resource_msg = ""
                            if arbitration_res.consumed_resource_type == "spell_slot" and arbitration_res.consumed_resource_name:
                                try:
                                    slots = json.loads(char.spell_slots)
                                    slot_name = str(arbitration_res.consumed_resource_name)
                                    if slot_name in slots and int(slots[slot_name]) > 0:
                                        slots[slot_name] = int(slots[slot_name]) - 1
                                        char.spell_slots = json.dumps(slots)
                                        needs_update = True
                                        resource_msg = f" (A consommé un emplacement de sort de niveau {slot_name})"
                                except Exception as e:
                                    logger.error(f"Error deducting spell slot: {e}")
                            elif arbitration_res.consumed_resource_type == "class_resource" and arbitration_res.consumed_resource_name:
                                try:
                                    resources = json.loads(char.class_resources)
                                    res_name = str(arbitration_res.consumed_resource_name)
                                    if res_name in resources and int(resources[res_name]) > 0:
                                        resources[res_name] = int(resources[res_name]) - 1
                                        char.class_resources = json.dumps(resources)
                                        needs_update = True
                                        resource_msg = f" (A consommé {res_name})"
                                except Exception as e:
                                    logger.error(f"Error deducting class resource: {e}")

                            # Apply HP change
                            if arbitration_res.hp_change != 0:
                                char.hp += arbitration_res.hp_change
                                # Clamp HP
                                char.hp = max(0, min(char.hp, char.max_hp))
                                needs_update = True

                            if needs_update:
                                session.add(char)
                                await session.commit()
                                await session.refresh(char)

                                # Parse fields back for frontend
                                known_spells_parsed = []
                                spell_slots_parsed = {}
                                class_resources_parsed = {}
                                try:
                                    known_spells_parsed = json.loads(char.known_spells)
                                    spell_slots_parsed = json.loads(char.spell_slots)
                                    class_resources_parsed = json.loads(char.class_resources)
                                except Exception:
                                    pass

                                # Broadcast STATS_UPDATE
                                await manager.send_personal_message(
                                    {
                                        "type": "stats_update",
                                        "character": {
                                            "id": str(char.id),
                                            "name": char.name,
                                            "hp": char.hp,
                                            "max_hp": char.max_hp,
                                            "armor_class": char.armor_class,
                                            "speed": char.speed,
                                            "reference_portrait_url": char.reference_portrait_url,
                                            "strength": char.strength,
                                            "dexterity": char.dexterity,
                                            "constitution": char.constitution,
                                            "intelligence": char.intelligence,
                                            "wisdom": char.wisdom,
                                            "charisma": char.charisma,
                                            "level": char.level,
                                            "experience": char.experience,
                                            "known_spells": known_spells_parsed,
                                            "spell_slots": spell_slots_parsed,
                                            "class_resources": class_resources_parsed
                                        }
                                    },
                                    websocket
                                )

                            arbitration_context = f"[Résultat du Système (NE PAS MONTRER AU JOUEUR)] : Le joueur a effectué une action. Le système a statué: {arbitration_res.narrative}. Succès: {arbitration_res.success}. Changement HP du joueur: {arbitration_res.hp_change}.{resource_msg}"
                        break # Only need one session
                # --- END ARBITRATION BLOCK ---

                # 1. Récupérer le personnage pour connaître son univers et son mode de jeu
                async for session in get_session():
                    import uuid
                    statement = select(Character).where(Character.id == uuid.UUID(player_id))
                    result = await session.execute(statement)
                    char = result.scalars().first()
                    game_session = await session.get(GameSession, uuid.UUID(session_id))
                    game_mode = game_session.game_mode if game_session else "NARRATIVE"
                    universe_id = char.universe_id if char else None

                    # 2. Récupération de la mémoire RAG (Lore), filtrée par univers
                    contexte_rag = await get_relevant_context(player_text, universe_id=universe_id, filter_type='lore')

                    # 3. Générer le texte du Narrateur
                    narrator_reply = await generate_narrator_response(session, player_id, player_text, context=contexte_rag + '\n\n' + arbitration_context, game_mode=game_mode)

                    if game_mode == "BATTLE":
                        from src.agents.narrator import get_combat_state
                        c_state = await get_combat_state(session, char.universe_id)
                        await manager.broadcast_to_session({
                            "type": "combat_state",
                            "entities": c_state,
                            "grid_width": game_session.grid_width if game_session else 15,
                            "grid_height": game_session.grid_height if game_session else 15,
        }, session_id)
                    break # Une seule session suffit

                # 4. Sauvegarder ce texte en BDD (UNE SEULE FOIS, via tâche asynchrone non-bloquante)
                task = asyncio.create_task(save_chat_message_background(None, "narrator", "narrator", narrator_reply, intent.intent.value))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

                # 5. Diffuser le texte via WebSocket
                await manager.broadcast_to_session(
                    {
                        "type": "narrator",
                        "category": intent.intent.value,
                        "message": narrator_reply
                    }, session_id
                )

                # 6. Appeler le scene_editor
                scene_decision = await analyze_scene(narrator_reply)

                # 7. SI ET SEULEMENT SI la décision est GENERATE, lancer la tâche asynchrone
                if scene_decision.decision == ImageDecision.GENERATE or scene_decision.decision.value == "GENERATE":
                    task = asyncio.create_task(background_image_generation(player_id, narrator_reply, manager, session_id))
                    background_tasks.add(task)
                    task.add_done_callback(background_tasks.discard)
                else:
                    logger.info("Scene editor decision: IGNORE")

                # 8. TTS: opt-in per session (GameSession.voice_enabled, default
                # False) -- costs a real OpenAI API call per narrator reply, so
                # skip entirely (no call, no cost) unless explicitly enabled.
                # narrator.py doesn't currently distinguish narration prose from
                # quoted NPC dialogue, so the whole reply is voiced as one clip
                # (source="narrator"); see audio_generator.py.
                if game_session is not None and game_session.voice_enabled:
                    task = asyncio.create_task(background_tts_generation(narrator_reply, manager, session_id, source="narrator"))
                    background_tasks.add(task)
                    task.add_done_callback(background_tasks.discard)

            elif intent.intent == IntentType.SYSTEM:
                # Ouverture d'une session de base de données asynchrone
                async for session in get_session():
                    narrator_reply = await generate_narrator_response(session, player_id, player_text)

                # Envoi du message au joueur concerné
                await manager.send_personal_message(

                    {

                        "type": "narrator",

                        "category": intent.intent.value,

                        "message": narrator_reply

                    },

                    websocket

                )

                # Save narrator personal message (background)
                task = asyncio.create_task(save_chat_message_background(player_id, "narrator", "narrator", narrator_reply, intent.intent.value))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"Erreur inattendue WebSocket pour {player_id}: {e}")
        manager.disconnect(websocket, session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
