import pytest
from uuid import uuid4
from sqlmodel import select
from src.engine.models import Character, Item
from src.engine.tools import execute_attack, move_entity, roll_dice

@pytest.mark.asyncio
async def test_execute_attack_with_weapon(db_session, monkeypatch):
    # Mock roll_dice pour avoir des résultats prévisibles
    def mock_roll_dice(notation: str) -> int:
        if "d20" in notation:
            return 20  # Toujours un coup critique/touche
        if "d8" in notation:
            return 8   # Max dégâts
        return 1

    monkeypatch.setattr("src.engine.tools.roll_dice", mock_roll_dice)

    attacker = Character(name="Attacker", hp=10, max_hp=10, armor_class=10, speed=30)
    target = Character(name="Target", hp=10, max_hp=10, armor_class=10, speed=30)

    db_session.add(attacker)
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(attacker)
    await db_session.refresh(target)

    weapon = Item(character_id=attacker.id, name="Sword", item_type="weapon", damage_dice="1d8")
    db_session.add(weapon)
    await db_session.commit()

    result_str = await execute_attack(db_session, attacker.id, target.id)

    await db_session.refresh(target)
    assert target.hp == 2  # 10 - 8
    assert "hits for 8 damage" in result_str

@pytest.mark.asyncio
async def test_execute_attack_unarmed_and_hp_not_negative(db_session, monkeypatch):
    def mock_roll_dice(notation: str) -> int:
        if "d20" in notation:
            return 20
        if "d4" in notation:
            return 4
        return 1

    monkeypatch.setattr("src.engine.tools.roll_dice", mock_roll_dice)

    attacker = Character(name="Attacker", hp=10, max_hp=10, armor_class=10, speed=30)
    target = Character(name="Weak Target", hp=2, max_hp=2, armor_class=10, speed=30)

    db_session.add(attacker)
    db_session.add(target)
    await db_session.commit()
    await db_session.refresh(attacker)
    await db_session.refresh(target)

    result_str = await execute_attack(db_session, attacker.id, target.id)

    await db_session.refresh(target)
    assert target.hp == 0  # 2 - 4 = -2, but bounded to 0
    assert "incapacitated" in result_str

@pytest.mark.asyncio
async def test_move_entity_success(db_session):
    char = Character(name="Mover", hp=10, max_hp=10, armor_class=10, speed=5, x=0, y=0)
    db_session.add(char)
    await db_session.commit()
    await db_session.refresh(char)

    # Move 3 steps right, 4 steps up (Chebyshev distance is max(3, 4) = 4 <= 5)
    result = await move_entity(db_session, char.id, 3, 4)

    await db_session.refresh(char)
    assert char.x == 3
    assert char.y == 4
    assert result["status"] == "success"

@pytest.mark.asyncio
async def test_move_entity_too_far(db_session):
    char = Character(name="Mover", hp=10, max_hp=10, armor_class=10, speed=5, x=0, y=0)
    db_session.add(char)
    await db_session.commit()
    await db_session.refresh(char)

    # Distance is max(6, 0) = 6 > 5
    with pytest.raises(ValueError, match="too far"):
        await move_entity(db_session, char.id, 6, 0)
