import re

with open("backend/src/engine/models.py", "r") as f:
    content = f.read()

# Ajouter la colonne à Character
content = re.sub(
    r"(y: int = Field\(default=0\))",
    r"\1\n    reference_portrait_url: Optional[str] = Field(default=None)",
    content
)

with open("backend/src/engine/models.py", "w") as f:
    f.write(content)
