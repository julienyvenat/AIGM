import re
import random
from uuid import UUID
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Character, Item

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
    attacker_statement = select(Character).where(Character.id == attacker_id).options(selectinload(Character.items))
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
    if attacker.items:
        for item in attacker.items:
            if item.item_type == "weapon" and item.damage_dice:
                weapon_dice = item.damage_dice
                break

    # Damage roll
    damage = roll_dice(weapon_dice)
    target.hp = max(0, target.hp - damage)
    session.add(target)
    await session.commit()

    if target.hp == 0:
        return f"{attacker.name} attacks {target.name} and hits for {damage} damage! {target.name} is incapacitated."

    return f"{attacker.name} attacks {target.name} and hits for {damage} damage! {target.name} has {target.hp} HP remaining."
