import json
import logging
import asyncio
from dotenv import load_dotenv

# Charger les variables d'environnement en premier
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from engine.database import init_db, get_session
from engine.models import ChatMessage
from sqlmodel import select, or_
from agents.router import analyze_player_intent, IntentType
from agents.narrator import generate_narrator_response
from memory.vector_db import get_relevant_context

from agents.scene_editor import analyze_scene, ImageDecision
from agents.image_prompter import generate_image_prompt
from pydantic import BaseModel
from engine.image_generator import generate_scene_image, download_image_locally
from engine.models import Character

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
            await manager.broadcast({
                "type": "scene_image",
                "url": image_url
            })
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
import os
from fastapi.staticfiles import StaticFiles
os.makedirs("backend/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="backend/images"), name="images")

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
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Nouvelle connexion WebSocket établie. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Connexion WebSocket fermée. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Envoie un message JSON à un joueur spécifique."""
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """Envoie un message JSON à tous les joueurs connectés."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi broadcast: {e}")

manager = ConnectionManager()



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

async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await manager.connect(websocket)

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
            sanitized_player_id = str(player_id).replace('\n', '\\n').replace('\r', '\\r')
            sanitized_player_text = str(player_text).replace('\n', '\\n').replace('\r', '\\r')
            logger.info(f"[{sanitized_player_id}] Dit: {sanitized_player_text}")

            # Save player message (background)
            task = asyncio.create_task(save_chat_message_background(player_id, "user", "chat", player_text))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

            # 2. Analyse de l'intention
            intent = analyze_player_intent(player_text)
            logger.info(f"[{player_id}] Intention détectée: {intent.intent.value} ({intent.action_type})")

            # 3. Aiguillage
            if intent.intent == IntentType.IGNORE:
                # On ne fait rien, on continue la boucle
                continue

            elif intent.intent in (IntentType.ROLEPLAY, IntentType.ACTION):
                # 1. Récupération de la mémoire RAG (Lore)
                contexte_rag = await get_relevant_context(player_text, filter_type='lore')

                # 2. Générer le texte du Narrateur
                async for session in get_session():
                    narrator_reply = await generate_narrator_response(session, player_id, player_text, context=contexte_rag)
                    break # Une seule session suffit

                # 3. Sauvegarder ce texte en BDD (UNE SEULE FOIS, via tâche asynchrone non-bloquante)
                task = asyncio.create_task(save_chat_message_background(None, "narrator", "narrator", narrator_reply, intent.intent.value))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)

                # 4. Diffuser le texte via WebSocket
                await manager.broadcast(
                    {
                        "type": "narrator",
                        "category": intent.intent.value,
                        "message": narrator_reply
                    }
                )

                # 5. Appeler le scene_editor
                scene_decision = await analyze_scene(narrator_reply)

                # 6. SI ET SEULEMENT SI la décision est GENERATE, lancer la tâche asynchrone
                if scene_decision.decision == ImageDecision.GENERATE or scene_decision.decision.value == "GENERATE":
                    task = asyncio.create_task(background_image_generation(player_id, narrator_reply, manager))
                    background_tasks.add(task)
                    task.add_done_callback(background_tasks.discard)
                else:
                    logger.info("Scene editor decision: IGNORE")

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
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erreur inattendue WebSocket pour {player_id}: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# Expose images directory to frontend
from fastapi.staticfiles import StaticFiles
import os

os.makedirs("backend/images", exist_ok=True)
app.mount("/images", StaticFiles(directory="backend/images"), name="images")
