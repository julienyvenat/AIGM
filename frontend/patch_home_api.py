with open('frontend/src/pages/Home.tsx', 'r') as f:
    content = f.read()

content = content.replace("import { useNavigate } from 'react-router-dom';", "import { useNavigate } from 'react-router-dom';\nimport { apiFetch } from '../utils/api';")

content = content.replace(
"fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/universes`)",
"apiFetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/universes`)"
)

with open('frontend/src/pages/Home.tsx', 'w') as f:
    f.write(content)
