import re

with open("backend/src/main.py", "r") as f:
    content = f.read()

# 1. Background image generator must use broadcast_to_session
img_gen = """async def background_image_generation(player_id: str, description: str, manager: "ConnectionManager", session_id: str):
    try:
        # Step 1: Tell frontend we are generating
        await manager.broadcast_to_session(
            {
                "type": "system",
                "category": "SYSTEM",
                "message": "🖼️ L'Architecte génère une image pour cette scène..."
            },
            session_id
        )"""

content = re.sub(
    r"async def background_image_generation\(player_id: str, description: str, manager: \"ConnectionManager\"\):\n    try:\n        # Step 1: Tell frontend we are generating\n        await manager\.broadcast\(\n            \{\n                \"type\": \"system\",\n                \"category\": \"SYSTEM\",\n                \"message\": \"🖼️ L'Architecte génère une image pour cette scène\.\.\.\"\n            \}\n        \)",
    img_gen,
    content
)

content = content.replace(
    'await manager.broadcast({\n            "type": "scene_image",\n            "url": image_url\n        })',
    'await manager.broadcast_to_session({\n            "type": "scene_image",\n            "url": image_url\n        }, session_id)'
)

# 2. Replace player_id with character_id inside the websocket endpoint loop
# For chat history:
chat_hist_repl = """    # Load and send chat history
    try:
        async for session in get_session():
            statement = select(ChatMessage).where(
                or_(ChatMessage.player_id == character_id, ChatMessage.player_id == None)
            ).order_by(ChatMessage.timestamp)"""

content = re.sub(
    r"    # Load and send chat history\n    try:\n        async for session in get_session\(\):\n            statement = select\(ChatMessage\)\.where\(\n                or_\(ChatMessage\.player_id == player_id, ChatMessage\.player_id == None\)\n            \)\.order_by\(ChatMessage\.timestamp\)",
    chat_hist_repl,
    content
)

# Exception block
content = re.sub(
    r"    except WebSocketDisconnect:\n        manager\.disconnect\(websocket\)\n    except Exception as e:\n        logger\.error\(f\"Erreur inattendue WebSocket pour \{player_id\}: \{e\}\"\)\n        manager\.disconnect\(websocket\)",
    """    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error(f"Erreur inattendue WebSocket pour {character_id}: {e}")
        manager.disconnect(websocket, session_id)""",
    content
)

# Inside the try/while loop:
content = content.replace("char_id = player_id", "char_id = character_id")
content = content.replace("f\"Player {player_id}", "f\"Player {character_id}")
content = content.replace("str(player_id)", "str(character_id)")
content = content.replace("Character.id == uuid.UUID(player_id)", "Character.id == uuid.UUID(character_id)")
content = content.replace("save_chat_message_background(player_id,", "save_chat_message_background(character_id,")
content = content.replace("generate_narrator_response(session, player_id,", "generate_narrator_response(session, character_id,")
content = content.replace("task = asyncio.create_task(generate_and_update_battlemap(player_id,", "task = asyncio.create_task(generate_and_update_battlemap(character_id,")

# 3. Replace all manager.broadcast with manager.broadcast_to_session
content = content.replace(
    'await manager.broadcast({',
    'await manager.broadcast_to_session({'
)
content = re.sub(r'await manager\.broadcast_to_session\(\{\n(.*?)\n\s*\}\)', r'await manager.broadcast_to_session({\n\1\n        }, session_id)', content, flags=re.DOTALL)

content = content.replace(
    '''                await manager.broadcast(
                    {
                        "type": "narrator",
                        "category": intent.intent.value,
                        "message": narrator_reply
                    }
                )''',
    '''                await manager.broadcast_to_session(
                    {
                        "type": "narrator",
                        "category": intent.intent.value,
                        "message": narrator_reply
                    }, session_id
                )'''
)

# Fix background task calls
content = content.replace(
    'task = asyncio.create_task(background_image_generation(character_id, narrator_reply, manager))',
    'task = asyncio.create_task(background_image_generation(character_id, narrator_reply, manager, session_id))'
)
content = content.replace(
    'task = asyncio.create_task(background_image_generation(player_id, narrator_reply, manager))',
    'task = asyncio.create_task(background_image_generation(character_id, narrator_reply, manager, session_id))'
)

with open("backend/src/main.py", "w") as f:
    f.write(content)
