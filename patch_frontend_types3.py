import os

files_to_update = {
    "frontend/src/pages/Dashboard.tsx": "import { Universe, GameSession, Character } from '../types';",
    "frontend/src/pages/Home.tsx": "import { Universe, Character } from '../types';",
    "frontend/src/pages/Play.tsx": "import { Character } from '../types';",
    "frontend/src/pages/Studio.tsx": "",
}

for filepath, correct_import in files_to_update.items():
    if not os.path.exists(filepath):
        continue

    with open(filepath, "r") as f:
        content = f.read()

    # Find and replace the import
    import_stmt = "import { Universe, GameSession, Character, GameSystem } from '../types';"
    content = content.replace(import_stmt, correct_import)

    with open(filepath, "w") as f:
        f.write(content)
