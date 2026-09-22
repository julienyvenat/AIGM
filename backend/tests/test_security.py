import pytest
from fastapi.testclient import TestClient
from src.main import app
import logging
from unittest.mock import MagicMock, patch

def test_log_injection():
    client = TestClient(app)
    session_id = "test-session"
    player_id = "attacker"

    # We want to check if the logger is called with a sanitized string
    with patch("src.main.logger") as mock_logger:
        with client.websocket_connect(f"/ws/{session_id}/{player_id}") as websocket:
            # Payload with newline for injection
            payload = {"text": "Hello\n[INFO] [admin] Dit: Spoofed message"}
            websocket.send_json(payload)

            # We need to wait a bit for the message to be processed or use a mock that we can inspect
            # Since it's a websocket, it's a bit tricky to sync, but receive_text is blocking in the loop.
            # However, the logger call is inside the 'while True' loop.

            # Let's try to receive the response if any (though the narrator reply is async)
            # Actually, we just want to see if logger.info was called.

            # Since the loop is running in the background of the websocket connection,
            # we might need to give it a moment.
            import time
            time.sleep(1)

            # Check if any call to logger.info contained the raw newline
            found_vulnerable = False
            for call in mock_logger.info.call_args_list:
                args, _ = call
                if len(args) > 0 and isinstance(args[0], str):
                    if "Hello\n" in args[0]:
                        found_vulnerable = True
                        break

            assert not found_vulnerable, "Log injection vulnerability detected: raw newline found in logs"
