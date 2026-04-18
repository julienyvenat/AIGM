with open("frontend/src/components/CharacterModal.tsx", "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "fetchUniverseEntities(" in line and "character.universe_id" in line:
        lines[i] = "      if (character.universe_id) { fetchUniverseEntities(character.universe_id as string); }\n"

with open("frontend/src/components/CharacterModal.tsx", "w") as f:
    f.writelines(lines)

with open("frontend/src/pages/Studio.tsx", "r") as f:
    content = f.read()

content = content.replace("GameSystemType[]", "GameSystem[]")
content = content.replace("import type { GameSystem } from '../types';\nimport { GameSystem as GameSystemType } from '../types';", "import { GameSystem } from '../types';")
content = content.replace("import type { GameSystem } from '../types';", "import { GameSystem } from '../types';")

with open("frontend/src/pages/Studio.tsx", "w") as f:
    f.write(content)
