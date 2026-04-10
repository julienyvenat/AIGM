with open('backend/src/main.py', 'r') as f:
    lines = f.readlines()

new_lines = []
app_line_idx = -1

for idx, line in enumerate(lines):
    if line.startswith('app = FastAPI('):
        app_line_idx = idx
        break

if app_line_idx != -1:
    # Need to move the new routes below app initialization
    with open('backend/src/main.py', 'r') as f:
        content = f.read()

    # Extract routes block
    import re
    routes_block = re.search(r'(class CharacterCreate.*?return {"status": "success", "message": "Joined session successfully"}\n)', content, flags=re.DOTALL)

    if routes_block:
        block = routes_block.group(1)
        content = content.replace(block, '')

        # Insert after app init
        app_init_idx = content.find('app = FastAPI(')
        next_empty_line = content.find('\n\n', app_init_idx) + 2

        content = content[:next_empty_line] + block + content[next_empty_line:]

        with open('backend/src/main.py', 'w') as f:
            f.write(content)
