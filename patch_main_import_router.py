with open("backend/src/main.py", "r") as f:
    content = f.read()
content = content.replace("from world_builder.world_router import router as world_router", "from src.world_builder.world_router import router as world_router")
with open("backend/src/main.py", "w") as f:
    f.write(content)
