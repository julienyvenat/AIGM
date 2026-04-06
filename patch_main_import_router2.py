with open("backend/src/main.py", "r") as f:
    content = f.read()
content = content.replace("from engine.database import", "from src.engine.database import")
content = content.replace("from engine.models import", "from src.engine.models import")
with open("backend/src/main.py", "w") as f:
    f.write(content)
