with open("frontend/src/pages/Studio.tsx", "r") as f:
    content = f.read()

# Revert my bad regex that messed up existing disables
content = content.replace("any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any // eslint-disable-line @typescript-eslint/no-explicit-any", "any[]>([]); // eslint-disable-line @typescript-eslint/no-explicit-any")

# And add the missing import for GameSystem in Studio if needed
if "GameSystem" not in content[:content.find("\n", content.find("import { "))]:
    content = content.replace("import { apiFetch } from '../utils/api';", "import { apiFetch } from '../utils/api';\nimport { GameSystem } from '../types';")


with open("frontend/src/pages/Studio.tsx", "w") as f:
    f.write(content)
