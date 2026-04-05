with open("frontend/src/components/CharacterModal.tsx", "r") as f:
    content = f.read()

content = content.replace(
    "character.known_spells.map((spell: any, idx: number) => {",
    "character.known_spells.map((spell: Record<string, unknown> | string, idx: number) => {"
)

with open("frontend/src/components/CharacterModal.tsx", "w") as f:
    f.write(content)

with open("frontend/src/pages/Studio.tsx", "r") as f:
    content = f.read()

content = content.replace("    // eslint-disable-next-line react-hooks/exhaustive-deps", "")

with open("frontend/src/pages/Studio.tsx", "w") as f:
    f.write(content)
