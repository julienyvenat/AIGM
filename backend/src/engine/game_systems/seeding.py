from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from src.engine.models import GameSystem
from src.engine.game_systems import srd52

DEFAULT_GAME_SYSTEM_NAME = srd52.SRD52_NAME
LEGACY_GAME_SYSTEM_NAME = "SRD 5e Light"


def _srd52_values() -> dict:
    return dict(
        description=srd52.SRD52_DESCRIPTION,
        rules_summary=srd52.SRD52_RULES_SUMMARY + "\n" + srd52.SRD52_ATTRIBUTION,
        core_rules_prompt=srd52.SRD52_CORE_RULES_PROMPT,
        character_schema=dict(srd52.SRD52_CHARACTER_SCHEMA),
        dice_system=srd52.SRD52_DICE_SYSTEM,
    )


async def ensure_default_game_systems(session: AsyncSession) -> List[GameSystem]:
    """Crée (ou met à jour) les systèmes de jeu intégrés. Idempotent."""
    result = await session.execute(select(GameSystem).where(GameSystem.name == srd52.SRD52_NAME))
    system = result.scalars().first()
    values = _srd52_values()
    if system is None:
        system = GameSystem(name=srd52.SRD52_NAME, **values)
    else:
        for key, value in values.items():
            setattr(system, key, value)
    session.add(system)
    await session.commit()
    await session.refresh(system)
    return [system]


async def get_default_game_system(session: AsyncSession) -> Optional[GameSystem]:
    """Système par défaut : SRD 5.2, à défaut l'ancien « SRD 5e Light »."""
    for name in (DEFAULT_GAME_SYSTEM_NAME, LEGACY_GAME_SYSTEM_NAME):
        result = await session.execute(select(GameSystem).where(GameSystem.name == name))
        system = result.scalars().first()
        if system:
            return system
    return None
