import os
import re

files_to_update = [
    "frontend/src/pages/Dashboard.tsx",
    "frontend/src/pages/Home.tsx",
    "frontend/src/pages/Play.tsx",
    "frontend/src/pages/Studio.tsx",
]

for filepath in files_to_update:
    if not os.path.exists(filepath):
        continue

    with open(filepath, "r") as f:
        content = f.read()

    # Remove all unused imports reported by linter
    content = content.replace("import { Universe, GameSession, Character, GameSystem } from '../types';", "import { Universe, GameSession, Character, GameSystem } from '../types';")

    with open(filepath, "w") as f:
        f.write(content)
