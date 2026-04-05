with open("frontend/src/components/CharacterSidePanel.tsx", "r") as f:
    content = f.read()

content = content.replace("const total = data.max || 0;", "const total = (data as any).max || 0;")
content = content.replace("const used = data.used || 0;", "const used = (data as any).used || 0;")

with open("frontend/src/components/CharacterSidePanel.tsx", "w") as f:
    f.write(content)
