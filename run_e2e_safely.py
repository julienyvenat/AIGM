import sys
import subprocess

try:
    result = subprocess.run([sys.executable, "test_e2e_game_flow.py"], env={"OPENAI_API_KEY": "dummy", "PYTHONPATH": "backend"}, capture_output=True, text=True, timeout=5)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
except subprocess.TimeoutExpired as e:
    print("Timeout!", e.stdout)
    print("STDERR:", e.stderr)
