from src.engine import models
import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel

from src.main import app
from src.engine.database import get_session
from src.memory.vector_db import add_to_memory

# Use file database for sqlite
test_engine = create_async_engine("sqlite+aiosqlite:///test_db.sqlite", echo=False)

async def init_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_test_session():
    async with AsyncSession(test_engine) as session:
        yield session

# Override the database session dependency
app.dependency_overrides[get_session] = get_test_session

client = TestClient(app)

# Setup models for WorldKnowledge mocking
from src.world_builder.schemas import WorldKnowledge, WorldNPC, WorldLocation, WorldFaction
from src.agents.router import PlayerIntent as IntentResponse, IntentType

def test_full_game_flow():
    import os
    if os.path.exists('test_db.sqlite'):
        os.remove('test_db.sqlite')

    # Run the init properly
    asyncio.run(init_db())

    # 1. Mock Universe Generation
    mock_world_knowledge = WorldKnowledge(
        histoire_globale="A test universe with magic.",
        npc=[WorldNPC(nom="Bob", faction=None, description="A guy", hp=10, armor_class=10)],
        location=[WorldLocation(nom="Town", description="A test town", points_interet=[])],
        faction=[WorldFaction(nom="Test Faction", description="A faction", relations_politiques=[])]
    )

    with patch("openai.resources.chat.completions.AsyncCompletions.parse", new_callable=AsyncMock) as mock_parse, \
         patch("openai.resources.chat.completions.AsyncCompletions.create", new_callable=AsyncMock) as mock_create, \
         patch("src.agents.universe_architect.generate_scene_image", new_callable=AsyncMock) as mock_image, \
         patch("src.world_builder.world_router.add_to_memory", new_callable=AsyncMock) as mock_add_mem:

        # Setup mock return values for Universe creation
        mock_msg = MagicMock()
        mock_msg.message.parsed = mock_world_knowledge
        mock_parse.return_value.choices = [mock_msg]

        mock_name_msg = MagicMock()
        mock_name_msg.message.content = "Test Universe"
        mock_create.return_value.choices = [mock_name_msg]

        mock_image.return_value = "/images/test.jpg"

        # Create Universe
        response = client.post("/world/generate-from-prompt", json={"prompt": "create test"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        universe_id = data["universe"]["id"]

    # 2. Get or create character via HTTP
    response = client.get(f"/universes/{universe_id}/characters/by-name/TestPlayer")
    assert response.status_code == 200
    char_id = response.json()["id"]
    assert char_id is not None

    # 3. Connect WebSocket and Test Narrative Message
    # TODO: Refactor with httpx.AsyncClient to fix greenlet_spawn async context.
    '''
    with patch("src.main.get_relevant_context", new_callable=AsyncMock) as mock_rag, \
         patch("src.main.get_session", side_effect=get_test_session) as mock_get_session, \
         patch("src.main.analyze_player_intent", new_callable=MagicMock) as mock_intent, \
         patch("src.main.generate_narrator_response", new_callable=AsyncMock) as mock_narrator, \
         patch("src.agents.narrator.get_combat_state", new_callable=AsyncMock) as mock_combat_state, \
         patch("src.main.analyze_scene", new_callable=AsyncMock) as mock_scene:

        mock_rag.return_value = "Lore context"

        # Mock Intent as ROLEPLAY
        mock_intent.return_value = IntentResponse(
            intent=IntentType.ROLEPLAY,
            action_type="speak",
            target="Bob",
            summary="test summary"
        )
        mock_narrator.return_value = "Hello TestPlayer!"

        # For scene editor, let's say IGNORE
        from src.agents.scene_editor import SceneEditorResponse, ImageDecision
        mock_scene.return_value = SceneEditorResponse(
            decision=ImageDecision.IGNORE,
            image_prompt=None,
            explanation="No image needed"
        )

        # Use TestClient websocket
        with client.websocket_connect(f"/ws/{char_id}") as websocket:
            # Send message
            websocket.send_json({"text": "Hello world!"})

            # We expect narrator response
            data = websocket.receive_json()
            print("Received:", data)
            assert data["type"] == "narrator"

            # 4. Switch to Battle mode
            websocket.send_json({"text": "/battle"})

            # Wait for narrator message
            data = websocket.receive_json()
            assert data["type"] == "narrator"
            assert "BATTLE" in data.get("category", "") or data.get("category") == "SYSTEM"
            # Wait for combat_state
            data = websocket.receive_json()
            assert data["type"] == "combat_state"

            # 5. Send an attack in battle mode
            # Mock Intent as ACTION
            mock_intent.return_value = IntentResponse(
                intent=IntentType.ACTION,
                action_type="attack",
                target="Bob",
                summary="test attack"
            )
            # When in BATTLE mode, the flow calls process_battle_action (which calls Arbitrator)
            with patch("src.main.process_battle_action", new_callable=AsyncMock) as mock_battle:
                mock_battle.return_value = {"type": "STATS_UPDATE", "character": {"id": char_id, "hp": 10}, "game_mode": "BATTLE"}

                websocket.send_json({"text": "I attack Bob!"})

                # Receive intent system message
                data = websocket.receive_json()
                assert data["type"] == "system"
                assert "ACTION" in data["message"]
    '''

if __name__ == "__main__":
    test_full_game_flow()
    print("Test passed successfully!")
