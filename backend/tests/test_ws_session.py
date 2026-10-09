"""
Tests for authentication/authorization on /ws/{session_id}/{player_id}.

The endpoint now requires a valid JWT, passed as a `token` query param
(browsers can't send custom WS headers, cf. AGENTS.md §7), AND requires that
the authenticated user actually owns the `player_id` Character they're
connecting as (src/main.py::websocket_endpoint, via
src/auth/deps.py::get_user_from_token). A missing/invalid/expired token, or
a valid token for a user who doesn't own that Character, must be rejected
with a close before the connection is ever accepted (code=1008) -- and must
never reach `manager.connect(...)`.

Like test_ws_reconnect.py, this seeds data through the *real* async engine
(`src.engine.database.engine`): the websocket endpoint loads its DB session
by calling `get_session()` directly rather than via FastAPI `Depends`, so
`app.dependency_overrides` has no effect on it.
"""
import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.auth.utils import create_access_token
from src.engine.database import engine as db_engine
from src.engine.models import Character, GameSession, GameSessionStatus, SessionParticipants, User
from src.main import app


def _seed_user_and_character(username: str):
    """Creates a User and a Character owned by them, plus an ACTIVE
    GameSession the character has joined (SessionParticipants), directly
    against the app's real database engine. Returns (user, character, game_session).
    """

    async def _setup():
        async with db_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            user = User(username=username, hashed_password="pw")
            session.add(user)
            await session.commit()
            await session.refresh(user)

            character = Character(
                name=f"{username}-hero", hp=10, max_hp=10, armor_class=10, speed=30,
                universe_id=uuid.uuid4(), user_id=user.id,
            )
            session.add(character)

            game_session = GameSession(universe_id=character.universe_id, status=GameSessionStatus.ACTIVE)
            session.add(game_session)
            await session.commit()
            await session.refresh(character)
            await session.refresh(game_session)

            session.add(SessionParticipants(character_id=character.id, session_id=game_session.id))
            await session.commit()

        return user, character, game_session

    return asyncio.run(_setup())


def test_ws_bad_token():
    """No token, and a garbage/unsigned token, must both be rejected."""
    _user, character, game_session = _seed_user_and_character("bad-token-user")

    with pytest.raises(Exception):
        with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}"):
            pass

    with pytest.raises(Exception):
        with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}?token=not-a-real-jwt"):
            pass


def test_ws_unknown_character_rejected():
    """A valid token is not enough on its own if the player_id doesn't
    resolve to any Character at all."""
    user, _character, game_session = _seed_user_and_character("orphan-token-user")
    token = create_access_token(user.id)

    with pytest.raises(Exception):
        with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{uuid.uuid4()}?token={token}"):
            pass


def test_ws_wrong_owner_rejected():
    """A valid token for user A trying to connect as a player_id belonging
    to user B's character must be rejected, even though the token itself
    verifies fine."""
    _owner, character, game_session = _seed_user_and_character("char-owner")
    intruder, _intruder_char, _intruder_session = _seed_user_and_character("intruder")

    intruder_token = create_access_token(intruder.id)

    with pytest.raises(Exception):
        with TestClient(app).websocket_connect(
            f"/ws/{game_session.id}/{character.id}?token={intruder_token}"
        ):
            pass


def test_ws_valid_owner_connects():
    """A valid token for the user who actually owns the character should be
    accepted."""
    user, character, game_session = _seed_user_and_character("valid-user")
    token = create_access_token(user.id)

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}?token={token}"):
        pass
