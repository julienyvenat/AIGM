import pytest
import os
import json
from unittest.mock import patch, MagicMock, AsyncMock

from src.agents.arbitrator import arbitrate_action, ArbitratorLLMOutput, ArbitratorResult
from src.engine.models import Character, GameSystem

@pytest.mark.asyncio
@patch('src.agents.arbitrator.gemini_client')
@patch('src.agents.arbitrator.LLM_PROVIDER', 'gemini')
async def test_arbitrate_action_gemini_system_prompt_contains_core_rules(mock_gemini_client):
    # Setup data
    game_system = GameSystem(
        name="Test System",
        description="A test system",
        rules_summary="These are the base rules.",
        core_rules_prompt="CORE RULES: Characters have a stamina pool.",
        dice_system="1d100",
        character_schema={}
    )
    character = Character(
        name="TestChar",
        hp=10, max_hp=10, armor_class=10, speed=30,
        universe_id="12345678-1234-5678-1234-567812345678",
        stats={"agility": 5}
    )
    intent_text = "I attack the goblin"

    # Mock chat session
    mock_chat = MagicMock()

    # Mock first response (no tool call)
    mock_response_1 = MagicMock()
    mock_response_1.function_calls = None
    mock_chat.send_message = AsyncMock(return_value=mock_response_1)
    mock_chat.get_history.return_value = []
    mock_gemini_client.aio.chats.create.return_value = mock_chat

    # Mock final generate_content response
    mock_response_final = MagicMock()
    mock_response_final.text = '{"action_type": "attack", "narrative": "Success", "success": true, "hp_change": 0, "consumed_resource_type": null, "consumed_resource_name": null}'
    mock_gemini_client.aio.models.generate_content = AsyncMock(return_value=mock_response_final)

    await arbitrate_action(character, game_system, intent_text)

    # Check that create was called with the right config
    assert mock_gemini_client.aio.chats.create.call_count == 1
    call_kwargs = mock_gemini_client.aio.chats.create.call_args.kwargs
    config = call_kwargs.get("config")

    assert config is not None
    system_instruction = config.system_instruction
    assert "CORE RULES: Characters have a stamina pool." in system_instruction
    assert '"agility": 5' in system_instruction

@pytest.mark.asyncio
@patch('src.agents.arbitrator.client')
@patch('src.agents.arbitrator.LLM_PROVIDER', 'openai')
async def test_arbitrate_action_openai_tools(mock_openai_client):
    game_system = GameSystem(
        name="Test System",
        description="A test system",
        rules_summary="These are the base rules.",
        core_rules_prompt="CORE RULES: Characters have a stamina pool.",
        dice_system="1d100",
        character_schema={}
    )
    character = Character(
        name="TestChar",
        hp=10, max_hp=10, armor_class=10, speed=30,
        universe_id="12345678-1234-5678-1234-567812345678",
        stats={"agility": 5}
    )

    # Setup mock to simulate a tool call, then a final response
    mock_msg1 = MagicMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "roll_dice"
    mock_tool_call.function.arguments = '{"expression": "1d20+3"}'
    mock_tool_call.id = "call_123"
    mock_msg1.tool_calls = [mock_tool_call]
    mock_msg1.content = None
    mock_msg1.role = "assistant"

    mock_resp1 = MagicMock()
    mock_resp1.choices = [MagicMock(message=mock_msg1)]

    mock_openai_client.chat.completions.create.return_value = mock_resp1

    mock_parsed_resp = MagicMock()
    mock_parsed_resp.action_type = "attack"
    mock_parsed_resp.narrative = "Success"
    mock_parsed_resp.success = True
    mock_parsed_resp.hp_change = 0
    mock_parsed_resp.consumed_resource_type = None
    mock_parsed_resp.consumed_resource_name = None

    mock_resp2 = MagicMock()
    mock_resp2.choices = [MagicMock(message=MagicMock(parsed=mock_parsed_resp))]
    mock_openai_client.beta.chat.completions.parse.return_value = mock_resp2

    result = await arbitrate_action(character, game_system, "I attack")

    assert result.success == True

    # Verify tools were provided to OpenAI
    call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
    assert "tools" in call_kwargs
    tools = call_kwargs["tools"]
    assert tools[0]["function"]["name"] == "roll_dice"

    # Verify system prompt
    system_msg = call_kwargs["messages"][0]["content"]
    assert "CORE RULES: Characters have a stamina pool." in system_msg
