import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from engine.database import init_db, get_session
from agents.router import analyze_player_intent, IntentType
from agents.narrator import generate_narrator_response
from memory.vector_db import get_relevant_context

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    logger.info("Initialisation de la base de données...")
    await init_db()
    yield
    # Arrêt
    logger.info("Arrêt de l'application...")

app = FastAPI(lifespan=lifespan)

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

@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await manager.connect(websocket)
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

            logger.info(f"[{player_id}] Dit: {player_text}")

            # 2. Analyse de l'intention
            intent = analyze_player_intent(player_text)
            logger.info(f"[{player_id}] Intention détectée: {intent.intent.value} ({intent.action_type})")

            # 3. Aiguillage
            if intent.intent == IntentType.IGNORE:
                # On ne fait rien, on continue la boucle
                continue

            elif intent.intent == IntentType.ROLEPLAY:
                # Récupération de la mémoire RAG
                contexte_rag = await get_relevant_context(player_text, filter_type='lore')
                # Appel de l'Agent Narrateur avec contexte
                async for session in get_session():
                    narrator_reply = await generate_narrator_response(session, player_id, player_text, context=contexte_rag)

                # Diffusion du message à tous les joueurs
                await manager.broadcast(
                    {
                        "type": "narrator",
                        "category": intent.intent.value,
                        "message": narrator_reply
                    }
                )

            elif intent.intent == IntentType.ACTION:
                # Ouverture d'une session de base de données asynchrone
                async for session in get_session():
                    narrator_reply = await generate_narrator_response(session, player_id, player_text)

                # Diffusion du message à tous les joueurs
                await manager.broadcast(
                    {
                        "type": "narrator",
                        "category": intent.intent.value,
                        "message": narrator_reply
                    }
                )

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

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Erreur inattendue WebSocket pour {player_id}: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
