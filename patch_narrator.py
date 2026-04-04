import re

with open("backend/src/agents/narrator.py", "r") as f:
    content = f.read()

# Add get_combat_state import dependencies
header_patch = """from sqlmodel import select
from engine.models import Character, WorldNPCTable"""

# We need to insert this near the top
content = content.replace("from engine.tools import move_entity, execute_attack, roll_dice",
                          "from engine.tools import move_entity, execute_attack, roll_dice\n" + header_patch)

# Add TACTICAL_SYSTEM_PROMPT
prompt_patch = """NARRATOR_SYSTEM_PROMPT = \"\"\"Tu es un Maître du Jeu de jeu de rôle. Tu gères le monde, l'histoire et les PNJ. Tu as accès à des outils pour interagir avec le moteur de jeu strict (déplacements, attaques, dés). Tu ne dois JAMAIS inventer le résultat d'une action mécanique, tu dois utiliser les outils pour ça, puis narrer le résultat de manière immersive et concise.\"\"\"

TACTICAL_SYSTEM_PROMPT = \"\"\"Tu es un MJ tactique. Ne fais plus de longue description narrative. Ta réponse doit être courte. Analyse la position des joueurs (X,Y) et des monstres. Utilise les règles de combat de D&D (mouvement, portée, actions). Décris uniquement le résultat des dés et les mouvements tactiques.\"\"\""""
content = content.replace("NARRATOR_SYSTEM_PROMPT = \"\"\"Tu es un Maître du Jeu de jeu de rôle. Tu gères le monde, l'histoire et les PNJ. Tu as accès à des outils pour interagir avec le moteur de jeu strict (déplacements, attaques, dés). Tu ne dois JAMAIS inventer le résultat d'une action mécanique, tu dois utiliser les outils pour ça, puis narrer le résultat de manière immersive et concise.\"\"\"", prompt_patch)

# Implement get_combat_state (for the tool) and add `game_mode` to `generate_narrator_response`
func_patch = """async def get_combat_state(session: AsyncSession, universe_id=None) -> list:
    \"\"\"Returns the combat state (entities with X, Y, HP, etc.)\"\"\"
    try:
        entities = []
        if universe_id:
            # Get PC
            st_char = select(Character).where(Character.universe_id == universe_id)
            res_char = await session.execute(st_char)
            chars = res_char.scalars().all()
            for c in chars:
                entities.append({
                    "id": str(c.id),
                    "name": c.name,
                    "is_pc": True,
                    "hp": c.hp,
                    "max_hp": c.max_hp,
                    "x": c.x,
                    "y": c.y
                })

            # Get NPCs in combat
            st_npc = select(WorldNPCTable).where(WorldNPCTable.universe_id == universe_id).where(WorldNPCTable.is_in_combat == True)
            res_npc = await session.execute(st_npc)
            npcs = res_npc.scalars().all()
            for npc in npcs:
                entities.append({
                    "id": str(npc.id),
                    "name": npc.nom,
                    "is_pc": False,
                    "hp": npc.hp if npc.hp else 10,
                    "max_hp": npc.hp if npc.hp else 10,
                    "x": npc.x,
                    "y": npc.y
                })
        return entities
    except Exception as e:
        import logging
        logging.error(f"Error in get_combat_state: {e}")
        return []

async def dispatch_tool_call"""
content = content.replace("async def dispatch_tool_call", func_patch)

tool_patch = """        if tool_name == "get_combat_state":
            # For the tool, we don't have universe_id easily accessible unless passed,
            # but usually they are all in one universe for solo MVP
            # We'll just fetch all or pass universe_id if needed, but it requires session
            # We actually rely on context passing in the narrator loop for awareness
            # But just in case, return a basic instruction
            return json.dumps({"message": "Combat state is provided in your system prompt context."})"""
content = content.replace("""        if tool_name == "get_combat_state":
            result = await get_combat_state(session)
            return json.dumps(result)""", tool_patch)

gen_patch = """async def generate_narrator_response(session: AsyncSession, player_id: str, text: str, context: str = "", game_mode: str = "NARRATIVE") -> str:
    system_instruction = NARRATOR_SYSTEM_PROMPT if game_mode != "BATTLE" else TACTICAL_SYSTEM_PROMPT

    # Append combat state to context if in battle
    if game_mode == "BATTLE":
        import uuid
        st = select(Character).where(Character.id == uuid.UUID(player_id))
        res = await session.execute(st)
        char = res.scalars().first()
        if char:
            combat_state = await get_combat_state(session, char.universe_id)
            context += "\\n\\n-- COMBAT STATE --\\n" + json.dumps(combat_state)

    if LLM_PROVIDER == "gemini":"""
content = content.replace("""async def generate_narrator_response(session: AsyncSession, player_id: str, text: str, context: str = "") -> str:
    if LLM_PROVIDER == "gemini":""", gen_patch)

gemini_sys_patch = """        if not gemini_client:
             raise ValueError("GOOGLE_API_KEY is not set.")

        if context:
            system_instruction += f"\\n\\nContext:\\n{context}\""""
content = content.replace("""        if not gemini_client:
             raise ValueError("GOOGLE_API_KEY is not set.")

        system_instruction = NARRATOR_SYSTEM_PROMPT
        if context:
            system_instruction += f"\\n\\nContext:\\n{context}\"""", gemini_sys_patch)

openai_sys_patch = """        if not client:
            raise ValueError("OPENAI_API_KEY not set.")

        messages = [{"role": "system", "content": system_instruction}]"""
content = content.replace("""        if not client:
            raise ValueError("OPENAI_API_KEY not set.")

        messages = [{"role": "system", "content": NARRATOR_SYSTEM_PROMPT}]""", openai_sys_patch)

with open("backend/src/agents/narrator.py", "w") as f:
    f.write(content)
