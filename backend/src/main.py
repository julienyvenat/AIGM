from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI(title="RPG AI GameMaster Backend")

# Configuration CORS pour autoriser les requêtes du frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production, par ex: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to the RPG AI GameMaster API"}

@app.websocket("/ws/{player_id}")
async def websocket_endpoint(websocket: WebSocket, player_id: str):
    await websocket.accept()
    print(f"Player {player_id} connected.")
    try:
        while True:
            # Réception du message sous forme de texte
            data = await websocket.receive_text()
            try:
                # Analyse du JSON
                message = json.loads(data)

                # Vérification de la présence d'un champ 'type'
                action_type = message.get("type", "unknown_action")
                payload = message.get("payload", {})

                print(f"Received action '{action_type}' from player {player_id}: {payload}")

                # Réponse de confirmation basique
                response = {
                    "status": "success",
                    "message": "Action received",
                    "received_type": action_type
                }
                await websocket.send_json(response)

            except json.JSONDecodeError:
                # Gestion des erreurs de parsing JSON
                error_response = {
                    "status": "error",
                    "message": "Invalid JSON format"
                }
                await websocket.send_json(error_response)

    except WebSocketDisconnect:
        print(f"Player {player_id} disconnected.")
