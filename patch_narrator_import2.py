with open("backend/src/agents/narrator.py", "r") as f:
    content = f.read()

# Add sqlmodel import correctly at the top
if "from sqlmodel import select" not in content:
    content = "from sqlmodel import select\nfrom engine.models import Character, WorldNPCTable\n" + content

with open("backend/src/agents/narrator.py", "w") as f:
    f.write(content)
