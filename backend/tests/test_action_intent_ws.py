"""
Regression test for a severe pre-existing bug: `main.py`'s WS handler called
`arbitrate_action(...)` in the ACTION-intent branch without ever importing it
(`arbitrate_action` is defined in `src.agents.arbitrator` and was only
imported by `tests/test_arbitrator.py`, which exercises it in isolation).

Any player message classified as ACTION intent (the core combat/mechanical
gameplay loop) hit a `NameError` at that call site. That `NameError` was only
caught by the outermost `except Exception` around the WS loop, which calls
`ConnectionManager.disconnect()` -- and `disconnect()` only forgets the
socket in server-side bookkeeping, it never calls `websocket.close()`. So the
player's connection went silently unresponsive with no close frame, which
from the frontend just looks like the game hung.

Unlike test_arbitrator.py (which imports and calls `arbitrate_action`
directly, so it never exercised the missing import in main.py), this test
goes through the real `/ws/...` endpoint and a real ACTION-classified
message, mocking only the LLM clients *inside* `src.agents.arbitrator`
(mirroring test_arbitrator.py's own patch targets) -- never
`src.main.arbitrate_action` itself, since patching that name would silently
inject it into `src.main`'s namespace and mask the exact bug this test
guards against.
"""
import asyncio
import uuid as uuid_module
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.agents.router import IntentType, PlayerIntent
from src.agents.scene_editor import ImageDecision, SceneEditorResponse
from src.auth.utils import create_access_token
from src.engine.database import engine as db_engine
from src.engine.models import Character, GameSession, GameSessionStatus, GameSystem, Universe, User
from src.main import app


@pytest.fixture()
def seeded_action_session():
    """Seeds a GameSystem/Universe/User/Character/GameSession against the
    app's real database engine (the WS endpoint bypasses `Depends`/
    `dependency_overrides`, see test_ws_reconnect.py). The Universe points at
    a real GameSystem so the ACTION branch's arbitration call gets a
    non-null `game_system` (main.py falls back to a "SRD 5e Light" lookup
    only when `universe.game_system_id` is unset)."""

    async def _setup():
        async with db_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            game_system = GameSystem(
                name=f"Action Test System {uuid_module.uuid4().hex[:8]}",
                description="A minimal test system.",
                rules_summary="Roll a d20.",
                core_rules_prompt="CORE RULES: roll d20 and compare to AC.",
                dice_system="1d20",
                character_schema={},
            )
            session.add(game_system)
            await session.commit()
            await session.refresh(game_system)

            universe = Universe(
                name="Action Test Universe", description="Un donjon hostile.",
                game_system_id=game_system.id,
            )
            session.add(universe)
            await session.commit()
            await session.refresh(universe)

            user = User(username=f"action-test-user-{uuid_module.uuid4().hex[:8]}", hashed_password="pw")
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

            await session.commit()
            await session.refresh(character)
            await session.refresh(game_session)

        return character, game_session, user

    return asyncio.run(_setup())


def test_action_intent_message_gets_a_real_response_not_a_hang(seeded_action_session, monkeypatch):
    """Sends a message that gets classified as ACTION intent through the
    real `/ws` handler and asserts the connection stays healthy and answers
    with a real narrator message, instead of silently going unresponsive."""
    character, game_session, user = seeded_action_session
    token = create_access_token(user.id)

    # 1. Force ACTION classification (this is what used to hit the missing
    #    `arbitrate_action` import).
    monkeypatch.setattr(
        "src.main.analyze_player_intent",
        lambda text: PlayerIntent(intent=IntentType.ACTION, summary="attaque le gobelin", target="gobelin", action_type="attack"),
    )

    # 2. Mock the LLM clients *inside* src.agents.arbitrator (same patch
    #    targets as test_arbitrator.py) so the REAL arbitrate_action runs
    #    end-to-end through main.py's real call site, without hitting a
    #    real OpenAI endpoint.
    mock_msg = MagicMock()
    mock_msg.tool_calls = None
    mock_msg.content = "no tool needed"
    mock_msg.role = "assistant"
    mock_first_response = MagicMock()
    mock_first_response.choices = [MagicMock(message=mock_msg)]

    mock_parsed = MagicMock()
    mock_parsed.action_type = "attack"
    mock_parsed.narrative = "Le coup porte, le gobelin est touché."
    mock_parsed.success = True
    mock_parsed.hp_change = 0
    mock_parsed.consumed_resource_type = None
    mock_parsed.consumed_resource_name = None
    mock_second_response = MagicMock()
    mock_second_response.choices = [MagicMock(message=MagicMock(parsed=mock_parsed))]

    mock_openai_client = MagicMock()
    mock_openai_client.chat.completions.create.return_value = mock_first_response
    mock_openai_client.beta.chat.completions.parse.return_value = mock_second_response

    # 3. Short-circuit the rest of the ROLEPLAY/ACTION narration pipeline
    #    (same pattern as test_voice_toggle.py/_mock_roleplay_pipeline) so
    #    only the arbitration call site under test does real work.
    monkeypatch.setattr("src.main.get_relevant_context", AsyncMock(return_value=""))
    monkeypatch.setattr("src.main.generate_narrator_response", AsyncMock(return_value="Le gobelin encaisse le coup et recule."))
    monkeypatch.setattr("src.main.analyze_scene", AsyncMock(return_value=SceneEditorResponse(decision=ImageDecision.IGNORE)))

    with patch("src.agents.arbitrator.client", mock_openai_client), \
         patch("src.agents.arbitrator.LLM_PROVIDER", "openai"):
        with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}?token={token}") as ws:
            ws.send_json({"text": "J'attaque le gobelin avec mon épée !"})

            # Pre-fix, the ACTION branch's `arbitrate_action(...)` call
            # raised NameError, which the outer `except Exception` in
            # main.py swallowed and turned into a silent, still-open but
            # unresponsive socket -- `receive_json()` would then hang/error
            # instead of ever getting this message.
            narrator_msg = ws.receive_json()
            assert narrator_msg["type"] == "narrator"
            assert narrator_msg["message"] == "Le gobelin encaisse le coup et recule."
            assert narrator_msg["category"] == "ACTION"

        # The real arbitrator LLM call path was actually exercised.
        mock_openai_client.chat.completions.create.assert_called_once()
        mock_openai_client.beta.chat.completions.parse.assert_called_once()
