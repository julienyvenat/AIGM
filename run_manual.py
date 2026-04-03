import asyncio
from engine.models import Character
from agents.arbitrator import arbitrate_action

async def main():
    c = Character(name="Test", hp=20, max_hp=20, armor_class=10, speed=30)
    res = await arbitrate_action(c, "Je me défends contre le piège")
    print(res)

if __name__ == "__main__":
    asyncio.run(main())
