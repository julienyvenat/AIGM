import os

files_to_update = [
    "frontend/src/components/CharacterManager.tsx",
    "frontend/src/components/CharacterModal.tsx",
    "frontend/src/components/CharacterSidePanel.tsx"
]

for filepath in files_to_update:
    with open(filepath, "r") as f:
        content = f.read()

    content = content.replace("import type { Character } from '../pages/Play';", "import type { Character } from '../types';")

    with open(filepath, "w") as f:
        f.write(content)


with open("frontend/src/components/CharacterModal.tsx", "r") as f:
    content = f.read()
content = content.replace("fetchUniverseEntities(character.universe_id);", "if (character.universe_id) fetchUniverseEntities(character.universe_id as string);")

with open("frontend/src/components/CharacterModal.tsx", "w") as f:
    f.write(content)
