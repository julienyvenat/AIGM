import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
import json

from src.agents.narrator import generate_narrator_response
from src.engine.models import Character, InventorySlot, Item, ItemType

@pytest.mark.asyncio
async def test_anti_cheat_inventory_injection():
    # 1. Setup a fake DB session with a character and an item
    class FakeSession:
        def __init__(self):
            self.char_id = uuid4()
            self.item = Item(id=uuid4(), universe_id=uuid4(), name="Epée Longue", item_type=ItemType.WEAPON)
            self.slot = InventorySlot(id=uuid4(), character_id=self.char_id, item_id=self.item.id, quantity=1, is_equipped=True)
            self.slot.item = self.item
            self.char = Character(id=self.char_id, universe_id=uuid4(), name="TestChar", hp=10, max_hp=10, armor_class=10, speed=30)
            self.char.inventory = [self.slot]

        async def execute(self, stmt):
            class FakeResult:
                def scalars(self):
                    class FakeScalars:
                        def first(inner_self):
                            return fake_session.char
                        def all(inner_self):
                            return [fake_session.char]
                    return FakeScalars()
            return FakeResult()

    fake_session = FakeSession()

    # 2. Mock the OpenAI client
    with patch("src.agents.narrator.client") as mock_client:
        mock_response = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Tu ne peux pas faire cela, tu n'as pas d'arc."
        mock_message.tool_calls = None
        mock_response.choices = [MagicMock(message=mock_message)]

        # AsyncMock for the completions create
        from unittest.mock import AsyncMock
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        # 3. Call the generator
        response_text = await generate_narrator_response(
            fake_session,
            str(fake_session.char_id),
            "Je tire une flèche avec mon arc sur le gobelin",
            context="",
            game_mode="NARRATIVE"
        )

        # 4. Assertions
        # Check that the mocked client was called
        mock_client.chat.completions.create.assert_called_once()

        # Extract the kwargs passed to the mock
        call_args = mock_client.chat.completions.create.call_args[1]
        messages = call_args['messages']

        # Verify the context was injected into the system prompt messages
        system_msgs = [m['content'] for m in messages if m['role'] == 'system']
        combined_system = " ".join(system_msgs)

        assert "SYSTEM_KNOWLEDGE - PLAYER INVENTORY" in combined_system
        assert "1x Epée Longue" in combined_system
        assert "Tu ne peux pas faire cela" in response_text
