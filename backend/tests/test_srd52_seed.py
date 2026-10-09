import pytest
from sqlmodel import select

from src.engine.game_systems import (
    DEFAULT_GAME_SYSTEM_NAME,
    ensure_default_game_systems,
    get_default_game_system,
)
from src.engine.models import GameSystem
from src.engine.services.character_service import validate_character_stats


@pytest.mark.asyncio
async def test_srd52_seed_is_idempotent(db_session):
    await ensure_default_game_systems(db_session)
    await ensure_default_game_systems(db_session)
    rows = (await db_session.execute(select(GameSystem))).scalars().all()
    assert [r.name for r in rows] == [DEFAULT_GAME_SYSTEM_NAME]
    assert "SRD 5.2" in rows[0].core_rules_prompt
    assert "CC" in rows[0].rules_summary or "Creative Commons" in rows[0].rules_summary


@pytest.mark.asyncio
async def test_default_system_and_schema(db_session):
    assert await get_default_game_system(db_session) is None
    await ensure_default_game_systems(db_session)
    gs = await get_default_game_system(db_session)
    assert gs.name == DEFAULT_GAME_SYSTEM_NAME
    stats = {k: 10 for k in gs.character_schema}
    validate_character_stats(stats, gs.character_schema)
