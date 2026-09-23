"""
Tests for Phase C voice (TTS) opt-in toggle: the `GameSession.voice_enabled`
flag (default False), the `PUT /sessions/{id}/voice` endpoint that flips it,
and the WS narrator flow only calling into TTS generation when it's True.

Mirrors the monkeypatch style used in test_battlemap_ws.py: mock the LLM/
scene-analysis calls out of the ROLEPLAY narration pipeline so only the
voice-toggle behavior under test is exercised, and never hit a real OpenAI
endpoint.
"""
import asyncio
import uuid as uuid_module
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.agents.router import IntentType, PlayerIntent
from src.agents.scene_editor import ImageDecision, SceneEditorResponse
from src.auth.utils import create_access_token
from src.engine.database import engine as db_engine
from src.engine.models import Character, GameSession, GameSessionStatus, Universe, User
from src.main import app


@pytest.fixture()
def seeded_session():
    """Seeds a Universe/User/Character/GameSession (NARRATIVE mode, host_id
    set to the user) against the app's real database engine -- the WS
    endpoint bypasses `Depends`/`dependency_overrides` (see
    test_ws_reconnect.py), so data must be seeded through the same engine."""

    async def _setup():
        async with db_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            universe = Universe(name="Voice Test Universe", description="Un royaume paisible.")
            session.add(universe)
            await session.commit()
            await session.refresh(universe)

            user = User(username=f"voice-test-user-{uuid_module.uuid4().hex[:8]}", hashed_password="pw")
            session.add(user)
            await session.commit()
            await session.refresh(user)

            character = Character(
                name="Hero", hp=10, max_hp=10, armor_class=10, speed=30,
                universe_id=universe.id, user_id=user.id,
            )
            session.add(character)

            game_session = GameSession(
                universe_id=universe.id, status=GameSessionStatus.ACTIVE, host_id=user.id,
            )
            session.add(game_session)

            await session.commit()
            await session.refresh(character)
            await session.refresh(game_session)

        return character, game_session, user

    return asyncio.run(_setup())


def _mock_roleplay_pipeline(monkeypatch):
    """Short-circuits everything in the ROLEPLAY narration pipeline except
    the voice_enabled branch under test: intent classification, narrator
    text generation, RAG context lookup and the scene-image decision are all
    stubbed so no real LLM/OpenAI call happens and no image generation task
    is spawned (that's covered separately by test_battlemap_ws.py)."""
    monkeypatch.setattr(
        "src.main.analyze_player_intent",
        lambda text: PlayerIntent(intent=IntentType.ROLEPLAY, summary="dit bonjour", target=None, action_type="dialogue"),
    )
    monkeypatch.setattr("src.main.generate_narrator_response", AsyncMock(return_value="Le tavernier vous sourit."))
    monkeypatch.setattr("src.main.get_relevant_context", AsyncMock(return_value=""))
    monkeypatch.setattr("src.main.analyze_scene", AsyncMock(return_value=SceneEditorResponse(decision=ImageDecision.IGNORE)))


def test_voice_disabled_by_default_skips_tts_generation(seeded_session, monkeypatch):
    character, game_session, user = seeded_session
    assert game_session.voice_enabled is False
    token = create_access_token(user.id)

    _mock_roleplay_pipeline(monkeypatch)
    tts_mock = AsyncMock(return_value="/audio/fake.mp3")
    monkeypatch.setattr("src.main.generate_speech_audio", tts_mock)

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}?token={token}") as ws:
        ws.send_json({"text": "Bonjour tavernier !"})

        narrator_msg = ws.receive_json()
        assert narrator_msg["type"] == "narrator"
        assert narrator_msg["message"] == "Le tavernier vous sourit."

    tts_mock.assert_not_called()


def test_voice_enabled_triggers_tts_generation_and_broadcast(seeded_session, monkeypatch):
    character, game_session, user = seeded_session
    token = create_access_token(user.id)

    # Enable voice via the same PUT endpoint the frontend toggle calls.
    with TestClient(app) as client:
        resp = client.put(
            f"/sessions/{game_session.id}/voice",
            json={"voice_enabled": True},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "success", "voice_enabled": True}

    _mock_roleplay_pipeline(monkeypatch)
    tts_mock = AsyncMock(return_value="/audio/fake.mp3")
    monkeypatch.setattr("src.main.generate_speech_audio", tts_mock)

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}?token={token}") as ws:
        ws.send_json({"text": "Bonjour tavernier !"})

        narrator_msg = ws.receive_json()
        assert narrator_msg["type"] == "narrator"

        audio_msg = ws.receive_json()
        assert audio_msg["type"] == "audio_ready"
        assert audio_msg["url"] == "/audio/fake.mp3"
        assert audio_msg["source"] == "narrator"

    tts_mock.assert_awaited_once_with("Le tavernier vous sourit.", filename_prefix="narrator")


def test_set_voice_enabled_rejects_non_host(seeded_session, monkeypatch):
    character, game_session, user = seeded_session

    async def _create_other_user():
        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            other = User(username=f"not-the-host-{uuid_module.uuid4().hex[:8]}", hashed_password="pw")
            session.add(other)
            await session.commit()
            await session.refresh(other)
            return other

    other_user = asyncio.run(_create_other_user())
    token = create_access_token(other_user.id)

    with TestClient(app) as client:
        resp = client.put(
            f"/sessions/{game_session.id}/voice",
            json={"voice_enabled": True},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert resp.status_code == 403
