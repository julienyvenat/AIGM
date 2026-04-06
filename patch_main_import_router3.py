with open("backend/src/main.py", "r") as f:
    content = f.read()
content = content.replace("from agents.", "from src.agents.")
content = content.replace("from engine.", "from src.engine.")
content = content.replace("from memory.", "from src.memory.")
with open("backend/src/main.py", "w") as f:
    f.write(content)
