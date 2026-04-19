import re

# Play.tsx - export interface Character is missing, or imported wrongly?
with open("frontend/src/pages/Play.tsx", "r") as f:
    content = f.read()

# Fix types import issue (verbatimModuleSyntax)
content = content.replace("import { GameSession } from '../types';", "import type { GameSession } from '../types';")
content = content.replace("import { Character } from '../types';", "import type { Character } from '../types';")

# Export it again in Play if other files use it
if "export interface Character" not in content and "interface Character {" in content:
    content = content.replace("interface Character {", "export interface Character {")

with open("frontend/src/pages/Play.tsx", "w") as f:
    f.write(content)


files_to_update = [
    "frontend/src/pages/Dashboard.tsx",
    "frontend/src/pages/Home.tsx",
    "frontend/src/pages/Studio.tsx",
    "frontend/src/components/RulebookModal.tsx",
]

for filepath in files_to_update:
    with open(filepath, "r") as f:
        content = f.read()

    content = re.sub(r"import\s+\{([^}]+)\}\s+from\s+'\.\./types';", r"import type { \1 } from '../types';", content)

    if filepath == "frontend/src/pages/Studio.tsx" and "import type { GameSystem } from '../types';" not in content:
        content = content.replace("import { apiFetch } from '../utils/api';", "import { apiFetch } from '../utils/api';\nimport type { GameSystem } from '../types';")

    with open(filepath, "w") as f:
        f.write(content)


# Fix CharacterModal string|undefined
with open("frontend/src/components/CharacterModal.tsx", "r") as f:
    content = f.read()

content = content.replace("fetchUniverseEntities(character.universe_id);", "if (character.universe_id) fetchUniverseEntities(character.universe_id);")

with open("frontend/src/components/CharacterModal.tsx", "w") as f:
    f.write(content)
