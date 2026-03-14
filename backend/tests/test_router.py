import pytest
import sys
import os

# Ensure backend directory is in the path for proper module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.router import analyze_player_intent, IntentType, PlayerIntent
from unittest.mock import patch, MagicMock

@patch('src.agents.router.client.beta.chat.completions.parse')
def test_analyze_player_intent_success(mock_parse):
    # Mocking a successful parse response
    mock_response = MagicMock()
    mock_parsed_content = PlayerIntent(
        intent=IntentType.ACTION,
        summary="Attaque au corps à corps",
        target="gobelin",
        action_type="attack"
    )
    mock_response.choices[0].message.parsed = mock_parsed_content
    mock_parse.return_value = mock_response

    result = analyze_player_intent("Je tape le gobelin")

    assert result['intent'] == IntentType.ACTION
    assert result['summary'] == "Attaque au corps à corps"
    assert result['target'] == "gobelin"
    assert result['action_type'] == "attack"

@patch('src.agents.router.client.beta.chat.completions.parse')
def test_analyze_player_intent_failure(mock_parse):
    # Mocking a failure (raising an exception)
    mock_parse.side_effect = Exception("API Error")

    result = analyze_player_intent("Je tape le gobelin")

    assert result['intent'] == IntentType.IGNORE
    assert result['summary'] == "Erreur de parsing"
    assert result['target'] is None
    assert result['action_type'] == "null"
