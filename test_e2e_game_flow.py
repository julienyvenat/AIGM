from src.engine import models
import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

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

# Setup models for WorldKnowledge mocking
from src.world_builder.schemas import WorldKnowledge, WorldNPC, WorldLocation, WorldFaction
from src.agents.router import PlayerIntent as IntentResponse, IntentType

@pytest.mark.asyncio
async def test_full_game_flow():
    import os
    if os.path.exists('test_db.sqlite'):
        os.remove('test_db.sqlite')

    # Run the init properly
    await init_db()

    # 1. Mock Universe Generation
    mock_world_knowledge = WorldKnowledge(
        histoire_globale="A test universe with magic.",
        npc=[WorldNPC(nom="Bob", faction=None, description="A guy", hp=10, armor_class=10)],
        location=[WorldLocation(nom="Town", description="A test town", points_interet=[])],
        faction=[WorldFaction(nom="Test Faction", description="A faction", relations_politiques=[])]
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
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
            response = await ac.post("/world/generate-from-prompt", json={"prompt": "create test"})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            universe_id = data["universe"]["id"]

        # 2. Get or create character via HTTP
        response = await ac.get(f"/universes/{universe_id}/characters/by-name/TestPlayer")
        assert response.status_code == 200
        char_id = response.json()["id"]
        assert char_id is not None

    # 3. Connect WebSocket and Test Narrative Message
    with patch("src.main.get_relevant_context", new_callable=AsyncMock) as mock_rag, \
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
        ws_client = TestClient(app)
        with ws_client.websocket_connect(f"/ws/{char_id}") as websocket:
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
            # In battle mode it might be tagged SYSTEM or have BATTLE in category
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
            # When in BATTLE mode, the flow calls arbitrate_action
            from src.agents.arbitrator import ArbitratorResult
            with patch("src.main.arbitrate_action", new_callable=AsyncMock) as mock_arbitrate:
                mock_arbitrate.return_value = ArbitratorResult(
                    roll_value=15,
                    modifier=2,
                    total=17,
                    success=True,
                    hp_change=0,
                    consumed_resource_type=None,
                    consumed_resource_name=None,
                    explanation="Hit!"
                )

                websocket.send_json({"text": "I attack Bob!"})

                # Receive narrator response
                data = websocket.receive_json()
                assert data["type"] == "narrator"
if __name__ == "__main__":
    # This is for manual execution
    # To run with pytest: PYTHONPATH=backend pytest test_e2e_game_flow.py
    asyncio.run(test_full_game_flow())
    print("Test passed successfully!")
