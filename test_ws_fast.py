import asyncio
import websockets
import json

async def test():
    async with websockets.connect("ws://localhost:8000/ws/90822edb-0883-45fb-92eb-f71101a037eb") as ws:
        await ws.recv() # history
        await ws.send(json.dumps({"text": "J'attaque le gobelin"}))
        for _ in range(5):
            res = json.loads(await asyncio.wait_for(ws.recv(), 10.0))
            print("GOT:", res.get("type"))
            if res.get("type") == "stats_update":
                print("SUCCESS")
                return

asyncio.run(test())
