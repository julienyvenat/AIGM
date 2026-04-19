import os
import re

files_to_update = [
    "frontend/src/pages/Dashboard.tsx",
    "frontend/src/pages/Home.tsx",
    "frontend/src/pages/Play.tsx",
    "frontend/src/pages/Studio.tsx",
]

for filepath in files_to_update:
    if not os.path.exists(filepath):
        continue

    with open(filepath, "r") as f:
        content = f.read()

    # Remove local interfaces
    content = re.sub(r'interface\s+Universe\s*{[^}]*}\n+', '', content)
    content = re.sub(r'interface\s+GameSession\s*{[^}]*}\n+', '', content)
    content = re.sub(r'export\s+interface\s+Character\s*{[^}]*}\n+', '', content)
    content = re.sub(r'interface\s+Character\s*{[^}]*}\n+', '', content)

    # Add imports
    import_match = re.search(r'import\s+.*?;', content)
    if import_match:
        import_stmt = "import { Universe, GameSession, Character, GameSystem } from '../types';\n"
        # ensure we don't add duplicate
        if "from '../types'" not in content:
            last_import = list(re.finditer(r'import\s+.*?;', content))[-1]
            content = content[:last_import.end()] + "\n" + import_stmt + content[last_import.end():]

    with open(filepath, "w") as f:
        f.write(content)
