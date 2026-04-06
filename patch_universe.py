import re

with open("backend/src/engine/models.py", "r") as f:
    content = f.read()

content = content.replace('sessions: List[GameSession] = Relationship(back_populates="universe")', 'sessions: List["GameSession"] = Relationship(back_populates="universe")')

with open("backend/src/engine/models.py", "w") as f:
    f.write(content)
