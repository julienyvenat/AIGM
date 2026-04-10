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

from src.engine.database import init_db, get_session
from sqlalchemy.ext.asyncio import AsyncSession
from src.engine.models import ChatMessage
from sqlmodel import select, or_
from src.agents.router import analyze_player_intent, IntentType
from src.agents.narrator import generate_narrator_response
from src.memory.vector_db import get_relevant_context

from src.agents.scene_editor import analyze_scene, ImageDecision
from src.agents.image_prompter import generate_image_prompt
from pydantic import BaseModel
from src.engine.image_generator import generate_scene_image, download_image_locally, generate_battlemap_prompt
from src.engine.models import Character, WorldNPCTable, User, GameSession, SessionParticipants
from src.auth.deps import get_current_user



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

async def background_image_generation(player_id: str, description: str, manager: "ConnectionManager"):
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
# Configuration CORS pour autoriser toutes les origines (développement local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
async def generate_portrait(request: PortraitRequest):
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

    except Exception as e:
        logger.error(f"Erreur generate_portrait: {e}")
        return {"error": str(e)}

@app.put("/characters/{character_id}/set-reference")
async def set_reference_portrait(character_id: str, request: ReferenceSetRequest):
    """Met à jour l'URL du portrait de référence d'un personnage."""
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from src.engine.database import get_session
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

async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await manager.connect(websocket)

    # Load and send chat history
    try:
        async for session in get_session():
            statement = select(ChatMessage).where(
                or_(ChatMessage.player_id == character_id, ChatMessage.player_id == None)
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
            async for session in get_session():
                import uuid
                statement = select(Character).where(Character.id == uuid.UUID(character_id))
                results = await session.execute(statement)
                char = results.scalars().first()
                if char and char.game_mode == "BATTLE" and char.battlemap_image_url:
                    await manager.send_personal_message(
                        {"type": "battlemap_update", "url": char.battlemap_image_url},
                        websocket
                    )

                    # Also send combat state
                    from src.agents.narrator import get_combat_state
                    combat_state = await get_combat_state(session, char.universe_id)
                    await manager.send_personal_message(
                        {"type": "combat_state", "entities": combat_state},
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
                player_text = payload.get("text")
                if not player_text:
                    raise ValueError("Le champ 'text' est manquant.")
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Message invalide de {player_id}: {e}")
                await manager.send_personal_message(
                    {"type": "error", "message": "Format de message invalide. Attendu: {'text': '...'}"},
                    websocket
                )
                continue # On ignore ce message et on attend le prochain

            # Sanitize player_id and player_text to prevent log injection
            sanitized_player_id = str(character_id).replace('\n', '\\n').replace('\r', '\\r')
            sanitized_player_text = str(player_text).replace('\n', '\\n').replace('\r', '\\r')
            logger.info(f"[{sanitized_player_id}] Dit: {sanitized_player_text}")

            # Save player message (background)
            task = asyncio.create_task(save_chat_message_background(character_id, "user", "chat", player_text))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

            if player_text.strip() == "/battle":
                import uuid
                async for session in get_session():
                    statement = select(Character).where(Character.id == uuid.UUID(character_id))
                    result = await session.execute(statement)
                    char = result.scalars().first()
                    if char:
                        char.game_mode = "BATTLE"
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

                        session.add(char)
                        await session.commit()

                        sys_msg = "The player just initiated combat. Describe the current environment and the enemies present in one short paragraph."
                        narrator_reply = await generate_narrator_response(session, character_id, sys_msg, game_mode="BATTLE")

                        await manager.broadcast_to_session({
                            "type": "narrator",
                            "category": "SYSTEM",
                            "message": narrator_reply
        }, session_id)

                        # Trigger battlemap generation
                        async def generate_and_update_battlemap(pid, desc, char_id):
                            bm_prompt = generate_battlemap_prompt(desc)
                            img_url = await generate_scene_image(bm_prompt)
                            if img_url:
                                local_url = await download_image_locally(img_url, "battlemap")
                                async for s in get_session():
                                    st = select(Character).where(Character.id == char_id)
                                    res = await s.execute(st)
                                    c = res.scalars().first()
                                    if c:
                                        c.battlemap_image_url = local_url
                                        s.add(c)
                                        await s.commit()
                                        await manager.broadcast_to_session({
                                            "type": "battlemap_update",
                                            "url": local_url
        }, session_id)
                                    break

                        task = asyncio.create_task(generate_and_update_battlemap(character_id, narrator_reply, char.id))
                        background_tasks.add(task)
                        task.add_done_callback(background_tasks.discard)

                        from src.agents.narrator import get_combat_state
                        c_state = await get_combat_state(session, char.universe_id)
                        await manager.broadcast_to_session({
                            "type": "combat_state",
                            "entities": c_state
        }, session_id)
                    break
                continue

            if player_text.strip() == "/endbattle":
                import uuid
                async for session in get_session():
                    statement = select(Character).where(Character.id == uuid.UUID(character_id))
                    result = await session.execute(statement)
                    char = result.scalars().first()
                    if char:
                        char.game_mode = "NARRATIVE"
                        char.battlemap_image_url = None

                        npc_statement = select(WorldNPCTable).where(WorldNPCTable.universe_id == char.universe_id).where(WorldNPCTable.is_in_combat == True)
                        npc_result = await session.execute(npc_statement)
                        npcs = npc_result.scalars().all()
                        for npc in npcs:
                            npc.is_in_combat = False
                            session.add(npc)

                        session.add(char)
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
                            "entities": []
        }, session_id)
                    break
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
                        statement = select(Character).where(Character.id == uuid.UUID(character_id))
                        result = await session.execute(statement)
                        char = result.scalars().first()

                        if char:
                            # Run arbitration
                            arbitration_res = await arbitrate_action(char, player_text)

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

                            arbitration_context = f"[Résultat du Système (NE PAS MONTRER AU JOUEUR)] : Le joueur a effectué une action. Le système a lancé un D20. Résultat du dé: {arbitration_res.roll_value}, Modificateur: {arbitration_res.modifier}, Total: {arbitration_res.total}. Succès: {arbitration_res.success}. Changement HP du joueur: {arbitration_res.hp_change}.{resource_msg}"
                        break # Only need one session
                # --- END ARBITRATION BLOCK ---

                # 1. Récupération de la mémoire RAG (Lore)
                contexte_rag = await get_relevant_context(player_text, universe_id=universe_id, filter_type='lore')

                # 2. Générer le texte du Narrateur
                async for session in get_session():
                    import uuid
                    statement = select(Character).where(Character.id == uuid.UUID(character_id))
                    result = await session.execute(statement)
                    char = result.scalars().first()
                    game_mode = char.game_mode if char else "NARRATIVE"

                    narrator_reply = await generate_narrator_response(session, character_id, player_text, context=contexte_rag + '\n\n' + arbitration_context, game_mode=game_mode)

                    if game_mode == "BATTLE":
                        from src.agents.narrator import get_combat_state
                        c_state = await get_combat_state(session, char.universe_id)
                        await manager.broadcast_to_session({
                            "type": "combat_state",
                            "entities": c_state
        }, session_id)
                    break # Une seule session suffit

                # 3. Sauvegarder ce texte en BDD (UNE SEULE FOIS, via tâche asynchrone non-bloquante)
                task = asyncio.create_task(save_chat_message_background(None, "narrator", "narrator", narrator_reply, intent.intent.value))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

                # 4. Diffuser le texte via WebSocket
                await manager.broadcast_to_session(
                    {
                        "type": "narrator",
                        "category": intent.intent.value,
                        "message": narrator_reply
                    }, session_id
                )

                # 5. Appeler le scene_editor
                scene_decision = await analyze_scene(narrator_reply)

                # 6. SI ET SEULEMENT SI la décision est GENERATE, lancer la tâche asynchrone
                if scene_decision.decision == ImageDecision.GENERATE or scene_decision.decision.value == "GENERATE":
                    task = asyncio.create_task(background_image_generation(character_id, narrator_reply, manager, session_id))
                    background_tasks.add(task)
                    task.add_done_callback(background_tasks.discard)
                else:
                    logger.info("Scene editor decision: IGNORE")

            elif intent.intent == IntentType.SYSTEM:
                # Ouverture d'une session de base de données asynchrone
                async for session in get_session():
                    narrator_reply = await generate_narrator_response(session, character_id, player_text)

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
                task = asyncio.create_task(save_chat_message_background(character_id, "narrator", "narrator", narrator_reply, intent.intent.value))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"Erreur inattendue WebSocket pour {character_id}: {e}")
        manager.disconnect(websocket, session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Expose images directory to frontend
from fastapi.staticfiles import StaticFiles
import os

os.makedirs("backend/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="backend/images"), name="images")
