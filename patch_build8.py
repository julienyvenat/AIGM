with open("frontend/src/pages/Studio.tsx", "r") as f:
    content = f.read()

content = content.replace("import type { GameSystem } from '../types';", "import { GameSystem } from '../types';")

with open("frontend/src/pages/Studio.tsx", "w") as f:
    f.write(content)
