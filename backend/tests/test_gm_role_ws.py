"""
Phase D: GameSession.gm_type (AI vs HUMAN game master) and the authority
model this drives in the WS handler.

Mirrors the established WS-test pattern (test_battlemap_ws.py /
test_voice_toggle.py / test_action_intent_ws.py): real seeded
User/Character/GameSession rows against the app's real (file-backed) DB
engine -- the WS endpoint bypasses `Depends`/`dependency_overrides`, see
test_ws_reconnect.py -- a real WS TestClient, and only the LLM-facing calls
mocked out.

Covered:
  (a) an AI-GM session (gm_type == GMType.AI, the default) behaves EXACTLY
      as before -- regression coverage, not just "new behavior added".
  (b) a HUMAN-GM session does NOT get autonomous AI narration/arbitration on
      a normal player message; it's broadcast as plain player chat instead.
  (c) the GM's on-demand consultation UI_ACTIONs (gm_consult_narrator,
      gm_consult_arbitrator) work and reply ONLY to the GM (personal
      message), never broadcast as authoritative.
  (d) a non-GM participant cannot trigger GM-only actions (/battle,
      gm_consult_narrator, gm_generate_scene) in a human-GM session.
  (e) the GM's own chat message is broadcast as authoritative narration
      with a distinguishing category/role, vs. a regular player's plain
      chat -- and reaches everyone at the table, including the GM.
"""
import asyncio
import uuid as uuid_module
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from src.agents.router import IntentType, PlayerIntent
from src.agents.scene_editor import ImageDecision, SceneEditorResponse
from src.auth.utils import create_access_token
from src.engine.database import engine as db_engine
from src.engine.models import Character, GameSession, GameSessionStatus, GameSystem, GMType, Universe, User
from src.main import app


def _mock_roleplay_pipeline(monkeypatch):
    """Same short-circuit as test_voice_toggle.py: stub the whole AI
    ROLEPLAY pipeline so a test can assert whether it ran at all, without
    ever hitting a real LLM/OpenAI endpoint."""
    monkeypatch.setattr(
        "src.main.analyze_player_intent",
        lambda text: PlayerIntent(intent=IntentType.ROLEPLAY, summary="dit bonjour", target=None, action_type="dialogue"),
    )
    monkeypatch.setattr("src.main.generate_narrator_response", AsyncMock(return_value="Le tavernier vous sourit."))
    monkeypatch.setattr("src.main.get_relevant_context", AsyncMock(return_value=""))
    monkeypatch.setattr("src.main.analyze_scene", AsyncMock(return_value=SceneEditorResponse(decision=ImageDecision.IGNORE)))


def _setup_session(gm_type: GMType, second_player: bool = False):
    async def _setup():
        async with db_engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            game_system = GameSystem(
                name=f"GM Role Test System {uuid_module.uuid4().hex[:8]}",
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
                name="GM Role Test Universe", description="Un royaume paisible.",
                game_system_id=game_system.id,
            )
            session.add(universe)
            await session.commit()
            await session.refresh(universe)

            host_user = User(username=f"gm-role-host-{uuid_module.uuid4().hex[:8]}", hashed_password="pw")
            session.add(host_user)
            await session.commit()
            await session.refresh(host_user)

            host_character = Character(
                name="Host Hero", hp=10, max_hp=10, armor_class=10, speed=30,
                universe_id=universe.id, user_id=host_user.id,
            )
            session.add(host_character)

            game_session = GameSession(
                universe_id=universe.id, status=GameSessionStatus.ACTIVE,
                host_id=host_user.id, gm_type=gm_type,
            )
            session.add(game_session)

            await session.commit()
            await session.refresh(host_character)
            await session.refresh(game_session)

            other_character = None
            other_user = None
            if second_player:
                other_user = User(username=f"gm-role-player-{uuid_module.uuid4().hex[:8]}", hashed_password="pw")
                session.add(other_user)
                await session.commit()
                await session.refresh(other_user)

                other_character = Character(
                    name="Other Hero", hp=10, max_hp=10, armor_class=10, speed=30,
                    universe_id=universe.id, user_id=other_user.id,
                )
                session.add(other_character)
                await session.commit()
                await session.refresh(other_character)

        return host_character, game_session, host_user, other_character, other_user

    return asyncio.run(_setup())


@pytest.fixture()
def ai_gm_session():
    return _setup_session(GMType.AI)


@pytest.fixture()
def human_gm_session():
    return _setup_session(GMType.HUMAN, second_player=True)


# --- (a) AI-GM regression coverage: gm_type == AI behaves exactly as before ---

def test_ai_gm_session_still_autonomously_narrates(ai_gm_session, monkeypatch):
    character, game_session, user, _, _ = ai_gm_session
    assert game_session.gm_type == GMType.AI
    token = create_access_token(user.id)

    _mock_roleplay_pipeline(monkeypatch)

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}?token={token}") as ws:
        ws.send_json({"text": "Bonjour tavernier !"})

        narrator_msg = ws.receive_json()
        assert narrator_msg["type"] == "narrator"
        assert narrator_msg["category"] == "ROLEPLAY"
        assert narrator_msg["message"] == "Le tavernier vous sourit."


def test_ai_gm_session_battle_command_still_works_for_any_participant(ai_gm_session, monkeypatch):
    """/battle is not gated at all when gm_type == AI (the default), for
    anyone connected -- exactly the pre-Phase-D behavior."""
    character, game_session, user, _, _ = ai_gm_session
    token = create_access_token(user.id)

    monkeypatch.setattr("src.main.generate_narrator_response", AsyncMock(return_value="Des gobelins surgissent !"))
    monkeypatch.setattr("src.main.generate_scene_image", AsyncMock(return_value=None))

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{character.id}?token={token}") as ws:
        ws.send_json({"text": "/battle"})
        narrator_msg = ws.receive_json()
        assert narrator_msg["type"] == "narrator"
        combat_msg = ws.receive_json()
        assert combat_msg["type"] == "combat_state"


# --- (b) HUMAN-GM: no autonomous AI narration/arbitration on a normal message ---

def test_human_gm_session_player_message_gets_no_autonomous_ai_response(human_gm_session, monkeypatch):
    _, game_session, host_user, other_character, other_user = human_gm_session
    assert game_session.gm_type == GMType.HUMAN
    token = create_access_token(other_user.id)

    # If the AI pipeline were still running, these would be called; assert
    # they never are.
    intent_mock = AsyncMock()
    monkeypatch.setattr("src.main.analyze_player_intent", intent_mock)
    narrator_mock = AsyncMock(return_value="Ceci ne devrait jamais être appelé.")
    monkeypatch.setattr("src.main.generate_narrator_response", narrator_mock)

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{other_character.id}?token={token}") as ws:
        ws.send_json({"text": "J'explore la taverne."})

        broadcast_msg = ws.receive_json()
        assert broadcast_msg["type"] == "chat"
        assert broadcast_msg["category"] == "PLAYER"
        assert broadcast_msg["message"] == "J'explore la taverne."
        assert broadcast_msg["player_id"] == str(other_character.id)

    intent_mock.assert_not_called()
    narrator_mock.assert_not_called()


def test_human_gm_own_message_is_broadcast_as_authoritative_narration(human_gm_session):
    host_character, game_session, host_user, _, _ = human_gm_session
    token = create_access_token(host_user.id)

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{host_character.id}?token={token}") as ws:
        ws.send_json({"text": "Le gobelin s'effondre, vaincu."})

        broadcast_msg = ws.receive_json()
        assert broadcast_msg["type"] == "narrator"
        assert broadcast_msg["category"] == "GM"
        assert broadcast_msg["role"] == "gm"
        assert broadcast_msg["message"] == "Le gobelin s'effondre, vaincu."


def test_human_gm_message_uses_broadcast_to_session_reaching_everyone(human_gm_session):
    """(e) 'broadcast to everyone including the GM': the GM's authoritative
    narration must actually reach a second, independently-connected
    WebSocket client -- not just be observed as a call to
    `manager.broadcast_to_session` with the right arguments. Two real WS
    connections (GM + another player) are opened simultaneously against the
    same session, following the same pattern already used safely in this
    file by test_gm_consult_narrator_replies_only_to_gm_and_is_not_broadcast,
    and both must receive the broadcast via real `receive_json()` calls."""
    host_character, game_session, host_user, other_character, other_user = human_gm_session
    host_token = create_access_token(host_user.id)
    other_token = create_access_token(other_user.id)

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{host_character.id}?token={host_token}") as host_ws, \
         TestClient(app).websocket_connect(f"/ws/{game_session.id}/{other_character.id}?token={other_token}") as player_ws:

        host_ws.send_json({"text": "Le coffre contient une potion."})

        host_msg = host_ws.receive_json()
        player_msg = player_ws.receive_json()

    for msg in (host_msg, player_msg):
        assert msg["type"] == "narrator"
        assert msg["category"] == "GM"
        assert msg["role"] == "gm"
        assert msg["message"] == "Le coffre contient une potion."


# --- (c) GM on-demand consultation: works, and is never auto-broadcast ---

def test_gm_consult_narrator_replies_only_to_gm_and_is_not_broadcast(human_gm_session):
    host_character, game_session, host_user, other_character, other_user = human_gm_session
    host_token = create_access_token(host_user.id)
    other_token = create_access_token(other_user.id)

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{host_character.id}?token={host_token}") as host_ws, \
         TestClient(app).websocket_connect(f"/ws/{game_session.id}/{other_character.id}?token={other_token}") as player_ws:

        from unittest.mock import AsyncMock as _AsyncMock
        import src.main as main_module
        original = main_module.generate_narrator_response
        main_module.generate_narrator_response = _AsyncMock(return_value="Suggestion : une ombre bouge dans le coin.")
        try:
            host_ws.send_json({
                "type": "UI_ACTION",
                "action": "gm_consult_narrator",
                "text": "Que se passe-t-il dans la taverne ?",
            })
            advisory = host_ws.receive_json()
        finally:
            main_module.generate_narrator_response = original

        assert advisory["type"] == "gm_advisory"
        assert advisory["advisory_type"] == "narrator"
        assert advisory["message"] == "Suggestion : une ombre bouge dans le coin."

        # Nothing was broadcast to the other player.
        player_ws.send_json({"text": "ping"})
        only_msg = player_ws.receive_json()
        assert only_msg["message"] == "ping"


def test_gm_consult_arbitrator_returns_advisory_result_without_applying_it(human_gm_session, monkeypatch):
    host_character, game_session, host_user, _, _ = human_gm_session
    token = create_access_token(host_user.id)

    from src.agents.arbitrator import ArbitratorResult
    mock_result = ArbitratorResult(
        action_type="attack", narrative="Le coup porte, 6 dégâts.", success=True, hp_change=-6,
        consumed_resource_type=None, consumed_resource_name=None,
    )
    monkeypatch.setattr("src.main.arbitrate_action", AsyncMock(return_value=mock_result))

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{host_character.id}?token={token}") as ws:
        ws.send_json({
            "type": "UI_ACTION",
            "action": "gm_consult_arbitrator",
            "entity_id": str(host_character.id),
            "text": "attaque le gobelin",
        })
        advisory = ws.receive_json()

    assert advisory["type"] == "gm_advisory"
    assert advisory["advisory_type"] == "arbitrator"
    assert advisory["result"]["narrative"] == "Le coup porte, 6 dégâts."
    assert advisory["result"]["hp_change"] == -6

    # Advisory only: the character's actual HP must be untouched.
    async def _reload_hp():
        async_session = sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            refreshed = await session.get(Character, host_character.id)
            return refreshed.hp

    assert asyncio.run(_reload_hp()) == 10


# --- (d) non-GM participants can't trigger GM-only actions in a HUMAN-GM session ---

def test_non_gm_participant_cannot_trigger_battle_mode(human_gm_session):
    _, game_session, _, other_character, other_user = human_gm_session
    token = create_access_token(other_user.id)

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{other_character.id}?token={token}") as ws:
        ws.send_json({"text": "/battle"})
        error_msg = ws.receive_json()
        assert error_msg["type"] == "error"


def test_non_gm_participant_cannot_use_gm_consult_narrator(human_gm_session):
    _, game_session, _, other_character, other_user = human_gm_session
    token = create_access_token(other_user.id)

    with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{other_character.id}?token={token}") as ws:
        ws.send_json({"type": "UI_ACTION", "action": "gm_consult_narrator", "text": "..."})
        error_msg = ws.receive_json()
        assert error_msg["type"] == "error"


def test_non_gm_participant_cannot_trigger_scene_generation(human_gm_session):
    _, game_session, _, other_character, other_user = human_gm_session
    token = create_access_token(other_user.id)

    image_mock = AsyncMock(return_value=None)
    import src.main as main_module
    original = main_module.background_image_generation
    main_module.background_image_generation = image_mock
    try:
        with TestClient(app).websocket_connect(f"/ws/{game_session.id}/{other_character.id}?token={token}") as ws:
            ws.send_json({"type": "UI_ACTION", "action": "gm_generate_scene", "description": "une taverne sombre"})
            error_msg = ws.receive_json()
            assert error_msg["type"] == "error"
    finally:
        main_module.background_image_generation = original
    image_mock.assert_not_called()
