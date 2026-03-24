import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from engine.models import Character
from engine.database import get_session, init_db

@pytest.mark.asyncio
async def test_set_reference_portrait():
    await init_db()
    # Insert a dummy character directly
    async for session in get_session():
        char = Character(name="TestHero", hp=10, max_hp=10, armor_class=10, speed=30)
        session.add(char)
        await session.commit()
        await session.refresh(char)
        char_id = str(char.id)
        break

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put(f"/characters/{char_id}/set-reference", json={"reference_portrait_url": "/images/test.png"})

    assert response.status_code == 200
    assert response.json() == {"status": "success", "reference_portrait_url": "/images/test.png"}
