import pytest
import uuid
import pytest_asyncio
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.engine.models import Character, Item, ItemType, InventorySlot, Universe
from src.engine.tools import grant_loot, equip_item, use_item

@pytest_asyncio.fixture
async def setup_data(db_session: AsyncSession):
    # Setup Universe
    univ = Universe(name="Test Universe", description="Test")
    db_session.add(univ)
    await db_session.commit()

    # Setup base items
    epee = Item(
        universe_id=univ.id,
        name="Épée Longue",
        description="Une lame tranchante",
        item_type=ItemType.WEAPON,
        attributes={"damage": "1d8", "slot": "hand"}
    )
    epee_courte = Item(
        universe_id=univ.id,
        name="Épée Courte",
        description="Une lame courte",
        item_type=ItemType.WEAPON,
        attributes={"damage": "1d6", "slot": "hand"}
    )
    dague = Item(
        universe_id=univ.id,
        name="Dague",
        description="Une petite lame",
        item_type=ItemType.WEAPON,
        attributes={"damage": "1d4", "slot": "hand"}
    )
    armure = Item(
        universe_id=univ.id,
        name="Armure de Cuir",
        description="Cuir souple",
        item_type=ItemType.ARMOR,
        attributes={"ac_bonus": 2, "slot": "torso"}
    )
    armure_clous = Item(
        universe_id=univ.id,
        name="Armure de Cuir Clouté",
        description="Cuir renforcé",
        item_type=ItemType.ARMOR,
        attributes={"ac_bonus": 3, "slot": "torso"}
    )
    potion = Item(
        universe_id=univ.id,
        name="Potion de Soin",
        description="Soigne les blessures",
        item_type=ItemType.CONSUMABLE,
        attributes={"healing": "2d4+2"}
    )

    db_session.add_all([epee, epee_courte, dague, armure, armure_clous, potion])

    # Setup character
    char = Character(name="Hero", hp=10, max_hp=10, armor_class=10, speed=30, universe_id=univ.id)
    db_session.add(char)
    await db_session.commit()

    return {
        "univ": univ,
        "char": char,
        "items": {
            "Épée Longue": epee,
            "Épée Courte": epee_courte,
            "Dague": dague,
            "Armure de Cuir": armure,
            "Armure de Cuir Clouté": armure_clous,
            "Potion de Soin": potion
        }
    }

@pytest.mark.asyncio
async def test_grant_loot(db_session: AsyncSession, setup_data: dict):
    char = setup_data["char"]

    # Test grant new item
    result = await grant_loot(db_session, char.id, "Potion de Soin", 1)
    assert result["status"] == "success"

    statement = select(InventorySlot).where(InventorySlot.character_id == char.id)
    results = await db_session.execute(statement)
    slots = results.scalars().all()

    assert len(slots) == 1
    assert slots[0].quantity == 1

    # Test increment existing item
    await grant_loot(db_session, char.id, "Potion de Soin", 2)

    results = await db_session.execute(statement)
    slots = results.scalars().all()
    assert len(slots) == 1
    assert slots[0].quantity == 3

@pytest.mark.asyncio
async def test_use_item_depletion(db_session: AsyncSession, setup_data: dict):
    char = setup_data["char"]
    potion = setup_data["items"]["Potion de Soin"]

    # Give 2 potions
    await grant_loot(db_session, char.id, "Potion de Soin", 2)

    # Use first potion
    result = await use_item(db_session, char.id, potion.id)
    assert result["status"] == "success"

    statement = select(InventorySlot).where(InventorySlot.character_id == char.id)
    results = await db_session.execute(statement)
    slots = results.scalars().all()
    assert len(slots) == 1
    assert slots[0].quantity == 1

    # Use second potion
    result = await use_item(db_session, char.id, potion.id)
    assert result["status"] == "success"

    # Assert slot is deleted
    results = await db_session.execute(statement)
    slots = results.scalars().all()
    assert len(slots) == 0

@pytest.mark.asyncio
async def test_equip_item_limits(db_session: AsyncSession, setup_data: dict):
    char = setup_data["char"]
    epee = setup_data["items"]["Épée Longue"]
    epee_courte = setup_data["items"]["Épée Courte"]
    dague = setup_data["items"]["Dague"]
    armure = setup_data["items"]["Armure de Cuir"]
    armure2 = setup_data["items"]["Armure de Cuir Clouté"]

    # Give weapons and armors
    await grant_loot(db_session, char.id, "Épée Longue", 1)
    await grant_loot(db_session, char.id, "Épée Courte", 1)
    await grant_loot(db_session, char.id, "Dague", 1)
    await grant_loot(db_session, char.id, "Armure de Cuir", 1)
    await grant_loot(db_session, char.id, "Armure de Cuir Clouté", 1)

    # Equip 1st Armor
    await equip_item(db_session, char.id, armure.id)

    # Equip 2nd Armor (should unequip 1st)
    await equip_item(db_session, char.id, armure2.id)

    # Verify Armors
    statement = select(InventorySlot).where(InventorySlot.character_id == char.id, InventorySlot.is_equipped == True)
    results = await db_session.execute(statement)
    equipped = results.scalars().all()

    equipped_armor = [s for s in equipped if s.item_id in (armure.id, armure2.id)]
    assert len(equipped_armor) == 1
    assert equipped_armor[0].item_id == armure2.id

    # Equip Weapons
    await equip_item(db_session, char.id, epee.id)
    await equip_item(db_session, char.id, epee_courte.id)

    results = await db_session.execute(statement)
    equipped = results.scalars().all()
    equipped_weapons = [s for s in equipped if s.item_id in (epee.id, epee_courte.id, dague.id)]
    assert len(equipped_weapons) == 2

    # Equip 3rd Weapon (should unequip one of the older weapons)
    await equip_item(db_session, char.id, dague.id)

    results = await db_session.execute(statement)
    equipped = results.scalars().all()
    equipped_weapons = [s for s in equipped if s.item_id in (epee.id, epee_courte.id, dague.id)]
    assert len(equipped_weapons) == 2
    # Ensure dague is equipped
    assert any(s.item_id == dague.id for s in equipped_weapons)
