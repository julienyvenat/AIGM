import asyncio
import uuid
from unittest.mock import patch, AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.main import app
from src.auth.utils import create_access_token
from src.engine.models import Character, GameSession, GameSessionStatus, SessionParticipants, User

engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _get_test_session():
    async with async_session_maker() as session:
        yield session


@pytest.fixture
def seeded_ids():
    async def init():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        async with async_session_maker() as session:
            user = User(username="attacker", hashed_password="pw")
            session.add(user)
            await session.commit()
            await session.refresh(user)

            char = Character(name="Hero", universe_id=uuid.uuid4(), user_id=user.id,
                             hp=10, max_hp=10, armor_class=10, speed=30)
            session.add(char)
            await session.commit()
            await session.refresh(char)

            game_session = GameSession(universe_id=char.universe_id, status=GameSessionStatus.ACTIVE)
            session.add(game_session)
            await session.commit()
            await session.refresh(game_session)

            session.add(SessionParticipants(session_id=game_session.id, character_id=char.id))
            await session.commit()
            return user.id, game_session.id, char.id

    user_id, session_id, char_id = asyncio.run(init())
    yield user_id, session_id, char_id

    async def teardown():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
    asyncio.run(teardown())


def test_ws_rejects_missing_token(seeded_ids):
    _, session_id, char_id = seeded_ids
    client = TestClient(app)
    with patch("src.main.get_session", _get_test_session):
        with pytest.raises(Exception):
            with client.websocket_connect(f"/ws/{session_id}/{char_id}"):
                pass


def test_log_injection(seeded_ids):
    user_id, session_id, char_id = seeded_ids
    token = create_access_token(subject=str(user_id))
    client = TestClient(app)

    with patch("src.main.get_session", _get_test_session), \
         patch("src.main.analyze_player_intent", AsyncMock(side_effect=RuntimeError("stop"))), \
         patch("src.main.logger") as mock_logger:
        with client.websocket_connect(f"/ws/{session_id}/{char_id}?token={token}") as websocket:
            websocket.send_json({"text": "Hello\n[INFO] [admin] Dit: Spoofed message"})
            import time
            time.sleep(1)

    logged = [call.args[0] for call in mock_logger.info.call_args_list
              if call.args and isinstance(call.args[0], str)]
    assert any("Dit: Hello" in msg for msg in logged), "Le message du joueur aurait dû être journalisé"
    assert not any("Hello\n" in msg for msg in logged), "Log injection : saut de ligne brut trouvé dans les logs"
