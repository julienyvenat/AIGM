import pytest
import sys
import os

# Ensure backend directory is in the path for proper module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.router import analyze_player_intent, IntentType, PlayerIntent
from unittest.mock import patch, MagicMock

@patch('src.agents.router.client')
def test_analyze_player_intent_success_openai(mock_client):
    # Mocking a successful parse response
    mock_response = MagicMock()
    mock_parsed_content = PlayerIntent(
        intent=IntentType.ACTION,
        summary="Attaque au corps à corps",
        target="gobelin",
        action_type="attack"
    )
    mock_response.choices[0].message.parsed = mock_parsed_content
    mock_client.beta.chat.completions.parse.return_value = mock_response

    result = analyze_player_intent("Je tape le gobelin")

    assert result.intent == IntentType.ACTION
    assert result.summary == "Attaque au corps à corps"
    assert result.target == "gobelin"
    assert result.action_type == "attack"

@patch('src.agents.router.client')
def test_analyze_player_intent_failure_openai(mock_client):
    # Mocking a failure (raising an exception)
    mock_client.beta.chat.completions.parse.side_effect = Exception("API Error")

    result = analyze_player_intent("Je tape le gobelin")

    assert result.intent == IntentType.IGNORE
    assert result.summary == "Erreur de parsing"
    assert result.target is None
    assert result.action_type == "null"

@patch('src.agents.router.gemini_client')
@patch('src.agents.router.LLM_PROVIDER', 'gemini')
def test_analyze_player_intent_success_gemini(mock_gemini_client):
    mock_response = MagicMock()
    mock_response.text = '{"intent": "ACTION", "summary": "Attaque au corps à corps", "target": "gobelin", "action_type": "attack"}'
    mock_gemini_client.models.generate_content.return_value = mock_response

    result = analyze_player_intent("Je tape le gobelin")

    assert result.intent == IntentType.ACTION
    assert result.summary == "Attaque au corps à corps"
    assert result.target == "gobelin"
    assert result.action_type == "attack"

@patch('src.agents.router.gemini_client')
@patch('src.agents.router.LLM_PROVIDER', 'gemini')
def test_analyze_player_intent_failure_gemini(mock_gemini_client):
    mock_gemini_client.models.generate_content.side_effect = Exception("API Error")

    result = analyze_player_intent("Je tape le gobelin")

    assert result.intent == IntentType.IGNORE
    assert result.summary == "Erreur de parsing"
    assert result.target is None
    assert result.action_type == "null"
