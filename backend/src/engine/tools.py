import re
import random
from uuid import UUID
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Character, Item, InventorySlot, ItemType

def roll_dice(notation: str) -> int:
    """Parse dice notation like '1d20+3' and return result."""
    notation = notation.lower().replace(" ", "")
    match = re.match(r"^(\d+)d(\d+)(?:([+-])(\d+))?$", notation)
    if not match:
        raise ValueError(f"Invalid dice notation: {notation}")

    num_dice = int(match.group(1))
    sides = int(match.group(2))
    modifier_sign = match.group(3)
    modifier_val = int(match.group(4)) if match.group(4) else 0

    total = sum(random.randint(1, sides) for _ in range(num_dice))

    if modifier_sign == "+":
        total += modifier_val
    elif modifier_sign == "-":
        total -= modifier_val

    return total

async def get_combat_state(session: AsyncSession) -> list[dict]:
    """Returns a list of all Characters with their coordinates and HP."""
    statement = select(Character)
    result = await session.execute(statement)
    characters = result.scalars().all()

    state = []
    for char in characters:
        state.append({
            "id": str(char.id),
            "name": char.name,
            "hp": char.hp,
            "max_hp": char.max_hp,
            "x": char.x,
            "y": char.y,
            "is_pc": char.is_pc,
            "reference_portrait_url": char.reference_portrait_url
        })
    return state

async def move_entity(session: AsyncSession, entity_id: UUID, target_x: int, target_y: int) -> dict:
    """Moves an entity checking Chebyshev distance."""
    char = await session.get(Character, entity_id)
    if not char:
        raise ValueError(f"Character {entity_id} not found")

    distance = max(abs(target_x - char.x), abs(target_y - char.y))
    if distance > char.speed:
        raise ValueError(f"Target is too far. Distance: {distance}, Speed: {char.speed}")

    char.x = target_x
    char.y = target_y
    session.add(char)
    await session.commit()

    return {
        "status": "success",
        "message": f"Moved {char.name} to ({target_x}, {target_y})"
    }

async def execute_attack(session: AsyncSession, attacker_id: UUID, target_id: UUID) -> str:
    """Executes an attack from attacker to target."""
    attacker_statement = select(Character).where(Character.id == attacker_id).options(
        selectinload(Character.inventory).selectinload(InventorySlot.item)
    )
    attacker_result = await session.execute(attacker_statement)
    attacker = attacker_result.scalars().first()

    target = await session.get(Character, target_id)

    if not attacker:
        raise ValueError(f"Attacker {attacker_id} not found")
    if not target:
        raise ValueError(f"Target {target_id} not found")

    # To hit roll
    attack_roll = roll_dice("1d20")
    # For simplicity, no attack modifier here, just base roll vs AC
    if attack_roll < target.armor_class:
        return f"{attacker.name} attacks {target.name} and misses! (Roll: {attack_roll} vs AC: {target.armor_class})"

    # Find weapon
    weapon_dice = "1d4" # default unarmed strike
    if attacker.inventory:
        for slot in attacker.inventory:
            if slot.is_equipped and slot.item and slot.item.item_type == ItemType.WEAPON:
                if slot.item.attributes and "damage" in slot.item.attributes:
                    weapon_dice = slot.item.attributes["damage"]
                    break

    # Damage roll
    damage = roll_dice(weapon_dice)
    target.hp = max(0, target.hp - damage)
    session.add(target)
    await session.commit()

    if target.hp == 0:
        return f"{attacker.name} attacks {target.name} and hits for {damage} damage! {target.name} is incapacitated."

    return f"{attacker.name} attacks {target.name} and hits for {damage} damage! {target.name} has {target.hp} HP remaining."

async def grant_loot(session: AsyncSession, character_id: UUID, item_name: str, quantity: int) -> dict:
    """Grants loot to a character by finding the item in the universe and updating the inventory slot."""
    char = await session.get(Character, character_id)
    if not char:
        raise ValueError(f"Character {character_id} not found")

    # Find item by name in the character's universe
    item_statement = select(Item).where(Item.universe_id == char.universe_id, Item.name == item_name)
    item_result = await session.execute(item_statement)
    item = item_result.scalars().first()

    if not item:
        raise ValueError(f"Item '{item_name}' not found in the universe.")

    # Check if character already has this item
    slot_statement = select(InventorySlot).where(
        InventorySlot.character_id == character_id,
        InventorySlot.item_id == item.id
    )
    slot_result = await session.execute(slot_statement)
    slot = slot_result.scalars().first()

    if slot:
        slot.quantity += quantity
        session.add(slot)
    else:
        slot = InventorySlot(character_id=character_id, item_id=item.id, quantity=quantity)
        session.add(slot)

    await session.commit()

    return {
        "status": "success",
        "message": f"Granted {quantity}x {item_name} to {char.name}."
    }

async def equip_item(session: AsyncSession, character_id: UUID, item_id: UUID) -> dict:
    """Equips an item for a character, respecting max 1 ARMOR and max 2 WEAPONS constraints."""
    char_statement = select(Character).where(Character.id == character_id).options(
        selectinload(Character.inventory).selectinload(InventorySlot.item)
    )
    char_result = await session.execute(char_statement)
    char = char_result.scalars().first()

    if not char:
        raise ValueError(f"Character {character_id} not found")

    # Find the specific slot we want to equip/unequip
    target_slot = None
    for slot in char.inventory:
        if slot.item_id == item_id:
            target_slot = slot
            break

    if not target_slot:
        raise ValueError(f"Character does not have item {item_id}")

    if not target_slot.item:
        raise ValueError(f"Item data missing for slot {target_slot.id}")

    # If currently equipped, just unequip it
    if target_slot.is_equipped:
        target_slot.is_equipped = False
        session.add(target_slot)
        await session.commit()
        return {"status": "success", "message": f"Unequipped {target_slot.item.name}"}

    # Cannot equip consumables or misc
    if target_slot.item.item_type not in (ItemType.WEAPON, ItemType.ARMOR):
        raise ValueError(f"Cannot equip item type {target_slot.item.item_type}")

    # Equip item and enforce constraints
    target_slot.is_equipped = True
    session.add(target_slot)

    equipped_weapons = []
    equipped_armor = []

    for slot in char.inventory:
        if slot.is_equipped and slot.item:
            if slot.item.item_type == ItemType.WEAPON:
                equipped_weapons.append(slot)
            elif slot.item.item_type == ItemType.ARMOR:
                equipped_armor.append(slot)

    # Sort them so we can unequip the oldest if we exceed the limit (assuming first found is older, or just unequip any other)
    # We will prioritize keeping the newly equipped item (target_slot)

    if target_slot.item.item_type == ItemType.ARMOR and len(equipped_armor) > 1:
        # Unequip other armors
        for slot in equipped_armor:
            if slot.id != target_slot.id:
                slot.is_equipped = False
                session.add(slot)

    elif target_slot.item.item_type == ItemType.WEAPON and len(equipped_weapons) > 2:
        # Unequip enough weapons to drop to 2, keep the target_slot equipped
        slots_to_unequip = len(equipped_weapons) - 2
        for slot in equipped_weapons:
            if slots_to_unequip <= 0:
                break
            if slot.id != target_slot.id:
                slot.is_equipped = False
                session.add(slot)
                slots_to_unequip -= 1

    await session.commit()
    return {"status": "success", "message": f"Equipped {target_slot.item.name}"}

async def use_item(session: AsyncSession, character_id: UUID, item_id: UUID) -> dict:
    """Uses a consumable item. Decrements quantity and deletes the slot if 0."""
    slot_statement = select(InventorySlot).where(
        InventorySlot.character_id == character_id,
        InventorySlot.item_id == item_id
    ).options(selectinload(InventorySlot.item))

    slot_result = await session.execute(slot_statement)
    slot = slot_result.scalars().first()

    if not slot:
        raise ValueError(f"Character does not have item {item_id}")

    if not slot.item:
        raise ValueError(f"Item data missing for slot {slot.id}")

    if slot.item.item_type != ItemType.CONSUMABLE:
        raise ValueError(f"Item {slot.item.name} is not a consumable.")

    # Apply logic
    # In a real game, you would parse slot.item.attributes to heal/buff etc.
    # We will just acknowledge the use here.

    slot.quantity -= 1

    message = f"Used {slot.item.name}."

    if slot.quantity <= 0:
        await session.delete(slot)
        message += " Item depleted and removed from inventory."
    else:
        session.add(slot)

    await session.commit()

    return {"status": "success", "message": message}
