import re

with open("backend/src/main.py", "r") as f:
    content = f.read()

manager_code = """class ConnectionManager:
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
        \"\"\"Envoie un message JSON à un joueur spécifique.\"\"\"
        await websocket.send_json(message)

    async def broadcast_to_session(self, message: dict, session_id: str):
        \"\"\"Envoie un message JSON à tous les joueurs connectés d'une session spécifique.\"\"\"
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi broadcast à la session {session_id}: {e}")
"""

# Replace the ConnectionManager class
content = re.sub(
    r"class ConnectionManager:.*?(?=\nmanager = ConnectionManager\(\))",
    manager_code,
    content,
    flags=re.DOTALL
)

with open("backend/src/main.py", "w") as f:
    f.write(content)
