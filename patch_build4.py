with open("frontend/src/types/index.ts", "r") as f:
    content = f.read()

if "inventory" not in content:
    content = content.replace("class_resources: Record<string, unknown>;", "class_resources: Record<string, unknown>;\n  inventory?: any[]; // eslint-disable-line @typescript-eslint/no-explicit-any")

with open("frontend/src/types/index.ts", "w") as f:
    f.write(content)

with open("frontend/src/pages/Studio.tsx", "r") as f:
    content = f.read()
if "import { GameSystem } from '../types';" not in content:
    content = content.replace("import type { GameSystem } from '../types';", "import type { GameSystem } from '../types';\nimport { GameSystem as GameSystemType } from '../types';")
    content = content.replace("useState<GameSystem[]>", "useState<GameSystemType[]>")

with open("frontend/src/pages/Studio.tsx", "w") as f:
    f.write(content)

with open("frontend/src/components/CharacterModal.tsx", "r") as f:
    content = f.read()
content = content.replace("if (character.universe_id) fetchUniverseEntities(character.universe_id as string);", "if (character.universe_id) { fetchUniverseEntities(character.universe_id as string); }")
content = content.replace("fetchUniverseEntities(character.universe_id as string);", "if (character.universe_id) { fetchUniverseEntities(character.universe_id as string); }")

# Fix string undefined manually
import re
content = re.sub(r'fetchUniverseEntities\(character\.universe_id\);', r'if (character.universe_id) fetchUniverseEntities(character.universe_id);', content)

with open("frontend/src/components/CharacterModal.tsx", "w") as f:
    f.write(content)
