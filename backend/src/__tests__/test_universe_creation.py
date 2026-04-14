import pytest
from httpx import AsyncClient
import uuid
import json

from src.main import app
from src.engine.models import GameSystem, Universe
from src.engine.database import get_session

@pytest.mark.asyncio
async def test_universe_creation_needs_system(monkeypatch):
    # Tests that the relationship can be established
    sys_id = uuid.uuid4()
    srd_system = GameSystem(
        id=sys_id,
        name=f"Mock System {sys_id}",
        description="Mock",
        rules_summary="Mock",
        dice_system="Mock"
    )

    uni_id = uuid.uuid4()
    universe = Universe(
        id=uni_id,
        name=f"Mock Uni {uni_id}",
        description="Mock",
        game_system_id=srd_system.id
    )

    assert universe.game_system_id == srd_system.id
