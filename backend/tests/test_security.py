import asyncio
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from src.auth.utils import create_access_token
from src.engine.database import engine as db_engine
from src.engine.models import Character, User
from src.main import app
import logging
from unittest.mock import MagicMock, patch


def _seed_authenticated_character():
    """Websocket connections now require a valid JWT owned by the
    connecting Character (see test_ws_session.py), so this test needs a
    real, authenticated user/character pair seeded against the endpoint's
    real DB engine (it calls get_session() directly, not via Depends)."""

    async def _setup():
        async with db_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            user = User(username="log-injection-user", hashed_password="pw")
            session.add(user)
            await session.commit()
            await session.refresh(user)

            character = Character(
                name="Attacker", hp=10, max_hp=10, armor_class=10, speed=30,
                universe_id=uuid.uuid4(), user_id=user.id,
            )
            session.add(character)
            await session.commit()
            await session.refresh(character)

        return user, character

    return asyncio.run(_setup())


def test_log_injection():
    client = TestClient(app)
    session_id = "test-session"
    user, character = _seed_authenticated_character()
    player_id = str(character.id)
    token = create_access_token(user.id)

    # We want to check if the logger is called with a sanitized string
    with patch("src.main.logger") as mock_logger:
        with client.websocket_connect(f"/ws/{session_id}/{player_id}?token={token}") as websocket:
            # Payload with newline for injection
            payload = {"text": "Hello\n[INFO] [admin] Dit: Spoofed message"}
            websocket.send_json(payload)

            # We need to wait a bit for the message to be processed or use a mock that we can inspect
            # Since it's a websocket, it's a bit tricky to sync, but receive_text is blocking in the loop.
            # However, the logger call is inside the 'while True' loop.

            # Let's try to receive the response if any (though the narrator reply is async)
            # Actually, we just want to see if logger.info was called.

            # Since the loop is running in the background of the websocket connection,
            # we might need to give it a moment.
            import time
            time.sleep(1)

            # Check if any call to logger.info contained the raw newline
            found_vulnerable = False
            for call in mock_logger.info.call_args_list:
                args, _ = call
                if len(args) > 0 and isinstance(args[0], str):
                    if "Hello\n" in args[0]:
                        found_vulnerable = True
                        break

            assert not found_vulnerable, "Log injection vulnerability detected: raw newline found in logs"
