import re

with open('backend/src/scripts/seed_data.py', 'r') as f:
    content = f.read()

# Add universe creation if we don't have it
if 'from src.engine.models import Character, Item, Universe' not in content:
    content = content.replace(
        'from src.engine.models import Character, Item',
        'from src.engine.models import Character, Item, Universe'
    )

new_uni = """    logger.info("Injecting SQL Entities (Characters and Items)...")

    uni_id = uuid.uuid4()
    uni = Universe(id=uni_id, name="Test Universe", description="A test")
    async for session in get_session():
        session.add(uni)
        await session.commit()
        break
"""

content = content.replace(
    '    logger.info("Injecting SQL Entities (Characters and Items)...")',
    new_uni
)

with open('backend/src/scripts/seed_data.py', 'w') as f:
    f.write(content)
