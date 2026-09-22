import uuid

import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.engine.models import Character, Universe, User
from src.engine.database import get_session, init_db
from src.auth.utils import create_access_token

@pytest.mark.asyncio
async def test_set_reference_portrait():
    await init_db()
    # Insert a dummy universe/user/character directly. `Character.universe_id`
    # is a required FK, and the route requires the caller to be the
    # character's owner (`char.user_id == current_user.id`), so both need to
    # be set up for the request to succeed.
    async for session in get_session():
        universe = Universe(name=f"Test Universe {uuid.uuid4()}", description="desc")
        session.add(universe)
        await session.commit()
        await session.refresh(universe)

        user = User(username=f"portrait_user_{uuid.uuid4()}", hashed_password="pw")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        char = Character(
            name="TestHero", hp=10, max_hp=10, armor_class=10, speed=30,
            universe_id=universe.id, user_id=user.id,
        )
        session.add(char)
        await session.commit()
        await session.refresh(char)
        char_id = str(char.id)
        break

    token = create_access_token(subject=str(user.id))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.put(
            f"/characters/{char_id}/set-reference",
            json={"reference_portrait_url": "/images/test.png"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "success", "reference_portrait_url": "/images/test.png"}
