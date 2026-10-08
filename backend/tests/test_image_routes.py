import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch

from src.main import app
from src.auth.deps import get_current_user
from src.engine.models import Character, Universe, User


@pytest.mark.asyncio
async def test_set_reference_portrait(db_session):
    universe = Universe(name="Test Universe", description="Universe for tests")
    user = User(username="portrait_owner", hashed_password="pw")
    db_session.add(universe)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(universe)
    await db_session.refresh(user)

    char = Character(universe_id=universe.id, user_id=user.id, name="TestHero",
                     hp=10, max_hp=10, armor_class=10, speed=30)
    db_session.add(char)
    await db_session.commit()
    await db_session.refresh(char)

    async def fake_get_session():
        yield db_session

    app.dependency_overrides[get_current_user] = lambda: user
    try:
        with patch("src.engine.database.get_session", fake_get_session):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"/characters/{char.id}/set-reference",
                    json={"reference_portrait_url": "/images/test.png"},
                )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json() == {"status": "success", "reference_portrait_url": "/images/test.png"}


@pytest.mark.asyncio
async def test_set_reference_portrait_forbidden_for_other_user(db_session):
    universe = Universe(name="Test Universe", description="Universe for tests")
    owner = User(username="real_owner", hashed_password="pw")
    intruder = User(username="intruder", hashed_password="pw")
    db_session.add_all([universe, owner, intruder])
    await db_session.commit()
    for obj in (universe, owner, intruder):
        await db_session.refresh(obj)

    char = Character(universe_id=universe.id, user_id=owner.id, name="TestHero",
                     hp=10, max_hp=10, armor_class=10, speed=30)
    db_session.add(char)
    await db_session.commit()
    await db_session.refresh(char)

    async def fake_get_session():
        yield db_session

    app.dependency_overrides[get_current_user] = lambda: intruder
    try:
        with patch("src.engine.database.get_session", fake_get_session):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                response = await ac.put(
                    f"/characters/{char.id}/set-reference",
                    json={"reference_portrait_url": "/images/hacked.png"},
                )
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 403
