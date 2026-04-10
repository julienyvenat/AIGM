with open('frontend/src/pages/Studio.tsx', 'r') as f:
    content = f.read()

if "import { apiFetch }" not in content:
    content = content.replace(
        "import { useNavigate } from 'react-router-dom';",
        "import { useNavigate } from 'react-router-dom';\nimport { apiFetch } from '../utils/api';"
    )
    with open('frontend/src/pages/Studio.tsx', 'w') as f:
        f.write(content)
