"""
Battlemap end-to-end WS tests: the `/battle` chat command and the
`move_entity` UI_ACTION (manual token drag-and-drop on the Battlemap).

Regression coverage: `/battle` and `/endbattle` used to set
`char.game_mode` / `char.battlemap_image_url`, but those fields live on
`GameSession`, not `Character` (see the on-connect resync code, and
test_ws_reconnect.py for the same class of bug already fixed there). Since
`Character` is a SQLModel/pydantic model, assigning an undeclared field
raises `ValueError`, which the broad `except Exception` around the WS loop
swallowed -- so `/battle` silently never actually entered battle mode. These
tests exercise the real WS message flow (not just the individual tool
functions) so that class of bug can't silently regress again.
"""
import asyncio
import uuid as uuid_module
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.auth.utils import create_access_token
from src.engine.database import engine as db_engine
from src.engine.models import Character, GameSession, GameSessionStatus, Universe, User, WorldNPCTable
from src.main import app


@pytest.fixture()
def seeded_narrative_session():
    """Seeds a Universe/User/Character/GameSession (still NARRATIVE mode)
    plus a couple of NPCs, directly against the app's real database engine
    (the WS endpoint bypasses `Depends`/`dependency_overrides`, see
    test_ws_reconnect.py)."""

    async def _setup():
        async with db_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            universe = Universe(name="Battle Test Universe", description="Une plaine hostile.")
            session.add(universe)
            await session.commit()
            await session.refresh(universe)

            # Unique per invocation: this fixture is (re)run once per test
            # function against the same real (file-backed) engine, which
            # would otherwise collide on the unique `username` constraint.
            user = User(username=f"battle-test-user-{uuid_module.uuid4().hex[:8]}", hashed_password="pw")
            session.add(user)
            await session.commit()
            await session.refresh(user)

            character = Character(
                name="Hero", hp=10, max_hp=10, armor_class=10, speed=30,
                universe_id=universe.id, user_id=user.id,
            )
            session.add(character)

            game_session = GameSession(universe_id=universe.id, status=GameSessionStatus.ACTIVE)
            session.add(game_session)

            npc1 = WorldNPCTable(universe_id=universe.id, nom="Gobelin 1", description="Un gobelin hargneux.")
            npc2 = WorldNPCTable(universe_id=universe.id, nom="Gobelin 2", description="Un gobelin hargneux.")
            session.add(npc1)
            session.add(npc2)

            await session.commit()
            await session.refresh(character)
            await session.refresh(game_session)

        return character, game_session, user

    return asyncio.run(_setup())


def test_battle_command_enters_battle_mode_and_broadcasts_grid(seeded_narrative_session, monkeypatch):
    character, game_session, user = seeded_narrative_session
    token = create_access_token(user.id)

    monkeypatch.setattr("src.main.generate_narrator_response", AsyncMock(return_value="Des gobelins surgissent !"))
    # Short-circuit the background battlemap image generation entirely --
    # not what this test is about, and it would need a mocked image pipeline.
    monkeypatch.setattr("src.main.generate_scene_image", AsyncMock(return_value=None))

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}?token={token}") as ws:
        ws.send_json({"text": "/battle"})

        narrator_msg = ws.receive_json()
        assert narrator_msg["type"] == "narrator"
        assert narrator_msg["message"] == "Des gobelins surgissent !"

        combat_msg = ws.receive_json()
        assert combat_msg["type"] == "combat_state"
        # The grid size now travels with combat_state instead of being a
        # frontend-hardcoded 15x15.
        assert isinstance(combat_msg["grid_width"], int)
        assert isinstance(combat_msg["grid_height"], int)
        names = {e["name"] for e in combat_msg["entities"]}
        assert "Hero" in names
        assert "Gobelin 1" in names


def test_move_entity_ui_action_persists_and_broadcasts_position(seeded_narrative_session, monkeypatch):
    character, game_session, user = seeded_narrative_session
    token = create_access_token(user.id)

    monkeypatch.setattr("src.main.generate_narrator_response", AsyncMock(return_value="Des gobelins surgissent !"))
    monkeypatch.setattr("src.main.generate_scene_image", AsyncMock(return_value=None))

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}?token={token}") as ws:
        ws.send_json({"text": "/battle"})
        ws.receive_json()  # narrator
        initial_combat_msg = ws.receive_json()  # combat_state
        assert initial_combat_msg["type"] == "combat_state"

        # Drag the player's own token to a new cell.
        ws.send_json({
            "type": "UI_ACTION",
            "action": "move_entity",
            "entity_id": str(character.id),
            "x": 3,
            "y": 4,
        })

        updated_combat_msg = ws.receive_json()
        assert updated_combat_msg["type"] == "combat_state"
        hero = next(e for e in updated_combat_msg["entities"] if e["name"] == "Hero")
        assert hero["x"] == 3
        assert hero["y"] == 4


def test_move_entity_ui_action_rejects_unknown_entity(seeded_narrative_session, monkeypatch):
    character, game_session, user = seeded_narrative_session
    token = create_access_token(user.id)

    monkeypatch.setattr("src.main.generate_narrator_response", AsyncMock(return_value="Des gobelins surgissent !"))
    monkeypatch.setattr("src.main.generate_scene_image", AsyncMock(return_value=None))

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}?token={token}") as ws:
        ws.send_json({"text": "/battle"})
        ws.receive_json()  # narrator
        ws.receive_json()  # combat_state

        ws.send_json({
            "type": "UI_ACTION",
            "action": "move_entity",
            "entity_id": "00000000-0000-0000-0000-000000000000",
            "x": 1,
            "y": 1,
        })

        error_msg = ws.receive_json()
        assert error_msg["type"] == "error"
