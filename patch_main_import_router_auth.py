import re

with open("backend/src/main.py", "r") as f:
    content = f.read()

# Add the import
content = content.replace('from src.world_builder.world_router import router as world_router\n', 'from src.world_builder.world_router import router as world_router\nfrom src.auth.router import auth_router\n')

# Add the router inclusion
content = content.replace('app.include_router(world_router)', 'app.include_router(world_router)\napp.include_router(auth_router)')

with open("backend/src/main.py", "w") as f:
    f.write(content)
