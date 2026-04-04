import re
with open("backend/src/agents/narrator.py", "r") as f:
    content = f.read()

content = content.replace(
    "from engine.tools import move_entity, execute_attack, roll_dice\nfrom sqlmodel import select\nfrom engine.models import Character, WorldNPCTable",
    "from sqlmodel import select\nfrom engine.models import Character, WorldNPCTable\nfrom engine.tools import move_entity, execute_attack, roll_dice"
)

# wait actually there's a typo in the previous patch, `from engine.tools import move_entity...` might be wrong.
