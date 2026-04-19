with open("frontend/src/components/CharacterModal.tsx", "r") as f:
    content = f.read()

# We might have double if statements due to replacements, clean them up
import re
content = re.sub(r'if \(character\.universe_id\) \{\s*if \(character\.universe_id\) \{\s*fetchUniverseEntities\(character\.universe_id as string\);\s*\}\s*\}', r'if (character.universe_id) { fetchUniverseEntities(character.universe_id as string); }', content)
content = re.sub(r'if \(character\.universe_id\) if \(character\.universe_id\) fetchUniverseEntities\(character\.universe_id as string\);', r'if (character.universe_id) fetchUniverseEntities(character.universe_id as string);', content)

# Check line 171 issue:
lines = content.split('\n')
for i, line in enumerate(lines):
    if "fetchUniverseEntities(" in line and "character.universe_id" in line:
         lines[i] = "      if (character.universe_id) { fetchUniverseEntities(character.universe_id); }"

with open("frontend/src/components/CharacterModal.tsx", "w") as f:
    f.write("\n".join(lines))
