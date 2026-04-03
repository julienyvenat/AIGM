import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)

async def test_websocket():
    uri = "ws://localhost:8000/ws/TestHero"
    try:
        async with websockets.connect(uri) as websocket:
            logging.info("Connected to WebSocket")

            # Attendre la réception de l'historique
            history = await websocket.recv()
            logging.info(f"Received history")

            # Envoyer une action simple meta
            action_msg = {"text": "Combien me reste-t-il de points de vie ?"}
            await websocket.send(json.dumps(action_msg))
            logging.info(f"Sent action: {action_msg}")

            # Écouter les réponses
            for _ in range(3):
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    resp_json = json.loads(response)
                    logging.info(f"Received response type: {resp_json.get('type')}")
                    if resp_json.get('type') == 'stats_update':
                        logging.info(f"Stats update received: {json.dumps(resp_json.get('character', {}), indent=2)}")
                except asyncio.TimeoutError:
                    logging.info("Timeout waiting for more messages")
                    break
    except Exception as e:
        logging.error(f"WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
