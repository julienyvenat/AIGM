import re

with open("backend/src/main.py", "r") as f:
    content = f.read()

# Add new imports
import_patch = """from engine.image_generator import generate_scene_image, download_image_locally, generate_battlemap_prompt
from engine.models import Character, WorldNPCTable"""
content = re.sub(r'from engine.image_generator import generate_scene_image, download_image_locally\nfrom engine.models import Character', import_patch, content)

# 1. Add connection logic to send current battle state
connection_patch = """                await manager.send_personal_message(
                    {"type": "history", "messages": history_payload},
                    websocket
                )

            # Send initial battle state if applicable
            async for session in get_session():
                import uuid
                statement = select(Character).where(Character.id == uuid.UUID(player_id))
                results = await session.execute(statement)
                char = results.scalars().first()
                if char and char.game_mode == "BATTLE" and char.battlemap_image_url:
                    await manager.send_personal_message(
                        {"type": "battlemap_update", "url": char.battlemap_image_url},
                        websocket
                    )

                    # Also send combat state
                    from agents.narrator import get_combat_state
                    combat_state = await get_combat_state(session, char.universe_id)
                    await manager.send_personal_message(
                        {"type": "combat_state", "entities": combat_state},
                        websocket
                    )
                break"""
content = content.replace("""                await manager.send_personal_message(
                    {"type": "history", "messages": history_payload},
                    websocket
                )""", connection_patch)

# 2. Add /battle and /endbattle intercept logic
intercept_patch = """            # Save player message (background)
            task = asyncio.create_task(save_chat_message_background(player_id, "user", "chat", player_text))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

            if player_text.strip() == "/battle":
                import uuid
                async for session in get_session():
                    statement = select(Character).where(Character.id == uuid.UUID(player_id))
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
                        narrator_reply = await generate_narrator_response(session, player_id, sys_msg, game_mode="BATTLE")

                        await manager.broadcast({
                            "type": "narrator",
                            "category": "SYSTEM",
                            "message": narrator_reply
                        })

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
                                        await manager.broadcast({
                                            "type": "battlemap_update",
                                            "url": local_url
                                        })
                                    break

                        task = asyncio.create_task(generate_and_update_battlemap(player_id, narrator_reply, char.id))
                        background_tasks.add(task)
                        task.add_done_callback(background_tasks.discard)

                        from agents.narrator import get_combat_state
                        c_state = await get_combat_state(session, char.universe_id)
                        await manager.broadcast({
                            "type": "combat_state",
                            "entities": c_state
                        })
                    break
                continue

            if player_text.strip() == "/endbattle":
                import uuid
                async for session in get_session():
                    statement = select(Character).where(Character.id == uuid.UUID(player_id))
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

                        await manager.broadcast({
                            "type": "system",
                            "message": "Le combat est terminé."
                        })
                        await manager.broadcast({
                            "type": "battlemap_update",
                            "url": None
                        })
                        await manager.broadcast({
                            "type": "combat_state",
                            "entities": []
                        })
                    break
                continue

            # 2. Analyse de l'intention"""
content = content.replace("""            # Save player message (background)
            task = asyncio.create_task(save_chat_message_background(player_id, "user", "chat", player_text))
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)

            # 2. Analyse de l'intention""", intercept_patch)

# 3. Update game_mode for generate_narrator_response
narrator_patch = """                # 2. Générer le texte du Narrateur
                async for session in get_session():
                    import uuid
                    statement = select(Character).where(Character.id == uuid.UUID(player_id))
                    result = await session.execute(statement)
                    char = result.scalars().first()
                    game_mode = char.game_mode if char else "NARRATIVE"

                    narrator_reply = await generate_narrator_response(session, player_id, player_text, context=contexte_rag + '\\n\\n' + arbitration_context, game_mode=game_mode)

                    if game_mode == "BATTLE":
                        from agents.narrator import get_combat_state
                        c_state = await get_combat_state(session, char.universe_id)
                        await manager.broadcast({
                            "type": "combat_state",
                            "entities": c_state
                        })
                    break # Une seule session suffit"""
content = content.replace("""                # 2. Générer le texte du Narrateur
                async for session in get_session():
                    narrator_reply = await generate_narrator_response(session, player_id, player_text, context=contexte_rag + '\\n\\n' + arbitration_context)
                    break # Une seule session suffit""", narrator_patch)

with open("backend/src/main.py", "w") as f:
    f.write(content)
