import pytest
from uuid import uuid4
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.engine.models import Character, GameSystem, Item, ItemType, WorldNPCTable, GameSession

def test_character_stats_json():
    char = Character(
        universe_id=uuid4(),
        name="Test Character",
        hp=10,
        max_hp=10,
        armor_class=10,
        speed=30,
        stats={"strength": 15, "dexterity": 14}
    )
    assert char.stats == {"strength": 15, "dexterity": 14}

def test_game_system_schema_json():
    gs = GameSystem(
        name="Test System",
        description="A test system",
        rules_summary="Some rules",
        dice_system="d20",
        core_rules_prompt="You are a GM.",
        character_schema={"str": "Strength", "dex": "Dexterity"}
    )
    assert gs.character_schema == {"str": "Strength", "dex": "Dexterity"}

def test_item_attributes_json():
    item = Item(
        universe_id=uuid4(),
        name="Test Item",
        item_type=ItemType.WEAPON,
        attributes={"damage": "1d6", "weight": 2.5}
    )
    assert item.attributes == {"damage": "1d6", "weight": 2.5}

def test_npc_combat_sheet_defaults_empty():
    # A bare-bones NPC (lore-only, not yet in combat) shouldn't need to
    # specify a combat sheet at all.
    npc = WorldNPCTable(
        universe_id=uuid4(),
        nom="Villageois",
        description="Un simple villageois.",
    )
    assert npc.resistances == []
    assert npc.vulnerabilities == []
    assert npc.actions == []

def test_npc_combat_sheet_json():
    # Game-agnostic JSON fields (AGENTS.md §8): damage types and action
    # shapes are whatever the game system calls them, never hardcoded.
    npc = WorldNPCTable(
        universe_id=uuid4(),
        nom="Golem de pierre",
        description="Un golem animé par la magie.",
        resistances=["tranchant", "perforant"],
        vulnerabilities=["feu"],
        actions=[{"name": "Poing de pierre", "damage": "2d6"}],
    )
    assert npc.resistances == ["tranchant", "perforant"]
    assert npc.vulnerabilities == ["feu"]
    assert npc.actions == [{"name": "Poing de pierre", "damage": "2d6"}]

def test_game_session_grid_defaults_match_previous_hardcoded_size():
    gs = GameSession(universe_id=uuid4())
    assert gs.grid_width == 15
    assert gs.grid_height == 15
