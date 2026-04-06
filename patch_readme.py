with open("README.md", "r") as f:
    content = f.read()

import re

# Remove the duplicated section
content = re.sub(r'## Configuration & Installation\n\n### Variables d\'environnement requises\nCréez un fichier `\.env` à la racine de `backend/` avec :\n```env\nOPENAI_API_KEY="votre_cle_openai"\nSECRET_KEY="votre_cle_secrete_pour_jwt" # par ex: `openssl rand -hex 32`\nALGORITHM="HS256"\nACCESS_TOKEN_EXPIRE_MINUTES=1440\n```\n\n### Authentification \(API\)\n- `POST /auth/register` : Créer un utilisateur \(`username`, `password`\)\.\n- `POST /auth/token` : S\'authentifier et récupérer un token JWT\.\n\n', '', content, count=1)

with open("README.md", "w") as f:
    f.write(content)
