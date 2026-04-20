import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.agents.image_prompter import generate_image_prompt
from src.agents.narrator import generate_narrator_response
from src.engine.image_generator import generate_scene_image
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
@patch('src.agents.image_prompter.gemini_client')
@patch('src.agents.image_prompter.LLM_PROVIDER', 'gemini')
async def test_generate_image_prompt_gemini(mock_gemini_client):
    mock_response = MagicMock()
    mock_response.text = '{"prompt": "A beautiful landscape"}'
    mock_gemini_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    result = await generate_image_prompt(MagicMock(), "player_id", "Un beau paysage")

    assert result == "A beautiful landscape"

@pytest.mark.asyncio
@patch('src.engine.image_generator.gemini_client')
@patch('src.engine.image_generator.IMAGE_PROVIDER', 'google')
async def test_generate_scene_image_gemini(mock_gemini_client):
    mock_result = MagicMock()
    mock_image = MagicMock()
    mock_image.image.image_bytes = b"fake_image_bytes"
    mock_result.generated_images = [mock_image]
    mock_gemini_client.models.generate_images.return_value = mock_result

    mock_file = AsyncMock()
    mock_file.__aenter__.return_value.write = AsyncMock()
    with patch('os.makedirs'), patch('aiofiles.open', return_value=mock_file):
        result = await generate_scene_image("A beautiful landscape")

    assert result is not None
    assert result.startswith("/images/")
