with open('frontend/src/pages/Dashboard.tsx', 'r') as f:
    content = f.read()

content = content.replace("import { useAuth } from '../hooks/useAuth';", "import { useAuth } from '../hooks/useAuth';\nimport { apiFetch } from '../utils/api';")

content = content.replace(
"""        const charsResponse = await fetch(`${baseUrl}/characters/`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });""",
"""        const charsResponse = await apiFetch(`${baseUrl}/characters/`);"""
)

content = content.replace(
"""        const sessionsResponse = await fetch(`${baseUrl}/sessions/`, {
           headers: {
            'Authorization': `Bearer ${token}`
          }
        });""",
"""        const sessionsResponse = await apiFetch(`${baseUrl}/sessions/`);"""
)

with open('frontend/src/pages/Dashboard.tsx', 'w') as f:
    f.write(content)
