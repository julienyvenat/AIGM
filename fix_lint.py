import re

# Fix useGameWebSocket.ts
with open("frontend/src/hooks/useGameWebSocket.ts", "r") as f:
    content = f.read()
content = content.replace("onStatsUpdate?: (character: any) => void", "onStatsUpdate?: (character: Record<string, unknown>) => void")
with open("frontend/src/hooks/useGameWebSocket.ts", "w") as f:
    f.write(content)

# Fix Play.tsx
with open("frontend/src/pages/Play.tsx", "r") as f:
    content = f.read()
content = content.replace("known_spells: any[];", "known_spells: Record<string, unknown>[];")
content = content.replace("spell_slots: Record<string, any>;", "spell_slots: Record<string, unknown>;")
content = content.replace("class_resources: Record<string, any>;", "class_resources: Record<string, unknown>;")
with open("frontend/src/pages/Play.tsx", "w") as f:
    f.write(content)

# Fix CharacterModal.tsx
with open("frontend/src/components/CharacterModal.tsx", "r") as f:
    content = f.read()
content = content.replace("const spellSlots = character.spell_slots as Record<string, any>;", "const spellSlots = character.spell_slots as Record<string, number>;")
with open("frontend/src/components/CharacterModal.tsx", "w") as f:
    f.write(content)
