import pytest
from uuid import uuid4
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.engine.models import Character, GameSystem, Item, ItemType

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
