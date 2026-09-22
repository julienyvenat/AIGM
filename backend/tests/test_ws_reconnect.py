"""
Regression test for the WebSocket reconnect bug.

The `/ws/{session_id}/{player_id}` endpoint (src/main.py::websocket_endpoint)
used to reference an undefined `character_id` variable (it should have been
`player_id`) while reloading chat history and initial battle state on
connect. That `NameError` (and, once fixed, a second bug where the code read
`game_mode`/`battlemap_image_url` off `Character` even though those fields
live on `GameSession`) was swallowed by a broad `except Exception` that only
logged the error, so no player ever actually received a history/battle-state
resync on (re)connect even though the connection itself looked healthy.

This test asserts the actual resync payloads are sent, not just that the
endpoint doesn't throw.
"""
import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.engine.database import engine as db_engine
from src.engine.models import (
    ChatMessage,
    Character,
    GameSession,
    GameSessionStatus,
    Universe,
    WorldNPCTable,
)
from src.main import app


@pytest.fixture()
def seeded_battle_session():
    """
    Seeds a Universe/Character/GameSession/ChatMessage/WorldNPCTable directly
    against the app's real database engine.

    The websocket endpoint calls `get_session()` directly (it isn't wired
    through FastAPI's `Depends`), so `app.dependency_overrides` has no effect
    on it and the data must be seeded through the same engine the endpoint
    itself uses.
    """

    async def _setup():
        async with db_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            universe = Universe(name="Test Universe", description="A universe for tests")
            session.add(universe)
            await session.commit()
            await session.refresh(universe)

            character = Character(
                name="Hero", hp=10, max_hp=10, armor_class=10, speed=30,
                universe_id=universe.id,
            )
            session.add(character)

            game_session = GameSession(
                universe_id=universe.id,
                status=GameSessionStatus.ACTIVE,
                game_mode="BATTLE",
                current_battlemap_url="http://example.com/battlemap.png",
            )
            session.add(game_session)

            npc = WorldNPCTable(
                universe_id=universe.id, nom="Goblin", description="A sneaky goblin",
                is_in_combat=True, x=3, y=4,
            )
            session.add(npc)
            await session.commit()
            await session.refresh(character)
            await session.refresh(game_session)

            chat_msg = ChatMessage(
                player_id=str(character.id),
                sender="user",
                type="chat",
                category="ROLEPLAY",
                content="Bonjour !",
            )
            session.add(chat_msg)
            await session.commit()

        return character, game_session

    return asyncio.run(_setup())


def test_reconnect_resends_chat_history_and_battle_state(seeded_battle_session):
    character, game_session = seeded_battle_session

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}") as ws:
        history_msg = ws.receive_json()
        assert history_msg["type"] == "history"
        contents = [m["message"] for m in history_msg["messages"]]
        assert "Bonjour !" in contents

        battlemap_msg = ws.receive_json()
        assert battlemap_msg["type"] == "battlemap_update"
        assert battlemap_msg["url"] == "http://example.com/battlemap.png"

        combat_msg = ws.receive_json()
        assert combat_msg["type"] == "combat_state"
        names = {entity["name"] for entity in combat_msg["entities"]}
        assert "Goblin" in names
        assert "Hero" in names
