with open('backend/src/main.py', 'r') as f:
    content = f.read()

content = content.replace(
    ', User, GameSession, SessionParticipants\nfrom src.auth.deps import get_current_user\n',
    ''
)
content = content.replace(
    'from src.engine.models import Character, WorldNPCTable',
    'from src.engine.models import Character, WorldNPCTable, User, GameSession, SessionParticipants\nfrom src.auth.deps import get_current_user'
)

with open('backend/src/main.py', 'w') as f:
    f.write(content)
