with open("backend/src/__tests__/test_universe_creation.py", "r") as f:
    content = f.read()

content = content.replace("async for session in get_session():", "from src.engine.database import init_db\n    await init_db()\n    async for session in get_session():")

with open("backend/src/__tests__/test_universe_creation.py", "w") as f:
    f.write(content)
