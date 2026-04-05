import re

with open("backend/src/engine/models.py", "r") as f:
    content = f.read()

# Character modifications
char_repl = r"""    experience: int = Field(default=0)

    game_mode: str = Field(default="NARRATIVE")
    battlemap_image_url: Optional[str] = Field(default=None)"""
content = re.sub(r'    experience: int = Field\(default=0\)', char_repl, content)

# NPC modifications
npc_repl = r"""    armor_class: Optional[int] = Field(default=None)
    x: int = Field(default=0)
    y: int = Field(default=0)
    is_in_combat: bool = Field(default=False)"""
content = re.sub(r'    armor_class: Optional\[int\] = Field\(default=None\)', npc_repl, content)

with open("backend/src/engine/models.py", "w") as f:
    f.write(content)
