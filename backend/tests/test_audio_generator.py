import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.engine.audio_generator import generate_speech_audio


@pytest.mark.asyncio
async def test_generate_speech_audio_success():
    mock_response = MagicMock()
    mock_response.aread = AsyncMock(return_value=b"fake_mp3_bytes")

    mock_client = MagicMock()
    mock_client.audio.speech.create = AsyncMock(return_value=mock_response)

    mock_file = AsyncMock()
    mock_file.__aenter__.return_value.write = AsyncMock()

    with patch("src.engine.audio_generator.client", mock_client), \
         patch("os.makedirs"), \
         patch("aiofiles.open", return_value=mock_file):
        result = await generate_speech_audio("Bienvenue, aventurier.", filename_prefix="narrator")

    assert result is not None
    assert result.startswith("/audio/narrator_")
    assert result.endswith(".mp3")
    mock_client.audio.speech.create.assert_awaited_once()
    _, kwargs = mock_client.audio.speech.create.call_args
    assert kwargs["input"] == "Bienvenue, aventurier."


@pytest.mark.asyncio
async def test_generate_speech_audio_no_api_key_returns_none():
    with patch("src.engine.audio_generator.client", None):
        result = await generate_speech_audio("Bienvenue, aventurier.")

    assert result is None


@pytest.mark.asyncio
async def test_generate_speech_audio_empty_text_returns_none_without_calling_api():
    mock_client = MagicMock()
    mock_client.audio.speech.create = AsyncMock()

    with patch("src.engine.audio_generator.client", mock_client):
        result = await generate_speech_audio("   ")

    assert result is None
    mock_client.audio.speech.create.assert_not_called()


@pytest.mark.asyncio
async def test_generate_speech_audio_api_error_returns_none():
    mock_client = MagicMock()
    mock_client.audio.speech.create = AsyncMock(side_effect=RuntimeError("boom"))

    with patch("src.engine.audio_generator.client", mock_client):
        result = await generate_speech_audio("Bienvenue, aventurier.")

    assert result is None
