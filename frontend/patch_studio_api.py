with open('frontend/src/pages/Studio.tsx', 'r') as f:
    content = f.read()

content = content.replace("import { useNavigate } from 'react-router-dom';", "import { useNavigate } from 'react-router-dom';\nimport { apiFetch } from '../utils/api';")

content = content.replace(
"const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/universes`);",
"const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/universes`);"
)

content = content.replace(
"""const res = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/world/generate-from-prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: universeDescription }),
      });""",
"""const res = await apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/world/generate-from-prompt`, {
        method: 'POST',
        body: JSON.stringify({ prompt: universeDescription }),
      });"""
)

with open('frontend/src/pages/Studio.tsx', 'w') as f:
    f.write(content)
