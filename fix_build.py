with open("frontend/src/components/CharacterModal.tsx", "r") as f:
    content = f.read()

content = content.replace("spell.name;", "(spell as Record<string, string>).name;")
content = content.replace("spell.description;", "(spell as Record<string, string>).description;")

with open("frontend/src/components/CharacterModal.tsx", "w") as f:
    f.write(content)

with open("frontend/src/components/CharacterSidePanel.tsx", "r") as f:
    content = f.read()

content = content.replace("const val = data.value;", "const val = (data as Record<string, number>).value;")
content = content.replace("const max = data.max;", "const max = (data as Record<string, number>).max;")

with open("frontend/src/components/CharacterSidePanel.tsx", "w") as f:
    f.write(content)
