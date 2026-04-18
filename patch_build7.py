with open("frontend/src/components/CharacterModal.tsx", "r") as f:
    content = f.read()

content = content.replace("['WEAPON', 'ARMOR'].includes(slot.item?.item_type)", "['WEAPON', 'ARMOR'].includes(slot.item?.item_type as string)")

with open("frontend/src/components/CharacterModal.tsx", "w") as f:
    f.write(content)

with open("frontend/src/pages/Studio.tsx", "r") as f:
    content = f.read()

if "import type { GameSystem } from '../types';" not in content and "import { GameSystem } from '../types';" not in content:
    content = content.replace("import { apiFetch } from '../utils/api';", "import { apiFetch } from '../utils/api';\nimport type { GameSystem } from '../types';")
elif "import { GameSystem } from '../types';" not in content:
    content = content.replace("import type { GameSystem } from '../types';", "import type { GameSystem } from '../types';")

with open("frontend/src/pages/Studio.tsx", "w") as f:
    f.write(content)
