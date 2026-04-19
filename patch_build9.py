with open("frontend/src/pages/Studio.tsx", "r") as f:
    content = f.read()

content = content.replace("import { apiFetch } from \"../utils/api\";\nimport { useState, useEffect } from 'react';", "import { apiFetch } from \"../utils/api\";\nimport { useState, useEffect } from 'react';\nimport type { GameSystem } from '../types';")

with open("frontend/src/pages/Studio.tsx", "w") as f:
    f.write(content)
