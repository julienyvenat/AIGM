import re

with open("backend/src/engine/tools.py", "r") as f:
    content = f.read()

# Ajouter la ligne dans get_combat_state
content = re.sub(
    r"(\"is_pc\": char\.is_pc)",
    r"\1,\n            \"reference_portrait_url\": char.reference_portrait_url",
    content
)

with open("backend/src/engine/tools.py", "w") as f:
    f.write(content)
