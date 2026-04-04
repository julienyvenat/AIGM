import asyncio
from sqlmodel import select, SQLModel
from engine.models import Character, WorldNPCTable, Universe
from engine.database import get_session, engine
from agents.narrator import get_combat_state

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)

async def test_battlemap_models():
    async for session in get_session():
        # Clean up
        u = Universe(name="test_univ", description="desc")
        session.add(u)
        await session.commit()
        await session.refresh(u)

        char = Character(name="Hero", hp=10, max_hp=10, armor_class=10, speed=30, universe_id=u.id)
        session.add(char)
        await session.commit()
        await session.refresh(char)

        assert char.game_mode == "NARRATIVE", "default game mode should be NARRATIVE"
        assert char.battlemap_image_url is None, "battlemap should be None"
        assert char.x == 0
        assert char.y == 0

        npc = WorldNPCTable(nom="Goblin", description="evil", universe_id=u.id)
        session.add(npc)
        await session.commit()
        await session.refresh(npc)

        assert npc.x == 0
        assert npc.y == 0
        assert npc.is_in_combat == False
        break

async def test_get_combat_state():
    async for session in get_session():
        u = Universe(name="test_univ2", description="desc2")
        session.add(u)
        await session.commit()
        await session.refresh(u)

        char = Character(name="Hero2", hp=10, max_hp=10, armor_class=10, speed=30, universe_id=u.id, x=5, y=5)
        npc = WorldNPCTable(nom="Goblin2", description="evil", universe_id=u.id, x=10, y=10, is_in_combat=True)
        session.add(char)
        session.add(npc)
        await session.commit()

        state = await get_combat_state(session, u.id)
        assert len(state) == 2, f"Expected 2 entities, got {len(state)}"

        names = [s["name"] for s in state]
        assert "Hero2" in names
        assert "Goblin2" in names
        break

async def main():
    await init_db()
    await test_battlemap_models()
    print("test_battlemap_models passed")
    await test_get_combat_state()
    print("test_get_combat_state passed")
    print("All tests passed.")

if __name__ == "__main__":
    asyncio.run(main())
