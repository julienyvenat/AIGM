# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

## Authentification & Routage Protégé (Phase 3)

Le frontend implémente maintenant un système complet d'authentification et de routage protégé.

### Fonctionnement

- **AuthContext** (`src/context/AuthContext.tsx`) :
  Gère l'état d'authentification global. Le token JWT (retourné par le backend) est sauvegardé dans le `localStorage`. Le contexte s'occupe de le charger, de le parser pour en extraire le `user`, et propose des fonctions de `login`, `register`, et `logout`.

- **ProtectedRoute** (`src/components/ProtectedRoute.tsx`) :
  Un composant qui enveloppe les routes privées (ex: `/dashboard`, `/studio`, `/play`). Si un utilisateur tente d'y accéder sans être authentifié, il est immédiatement redirigé vers `/login`.

- **Dashboard** (`src/pages/Dashboard.tsx`) :
  Point d'entrée pour un joueur connecté, permettant de retrouver la liste de ses personnages et de rejoindre les sessions en cours.

- **WebSocket Protégé** (`src/hooks/useGameWebSocket.ts`) :
  Le flux WebSocket utilise maintenant l'identifiant de la session, l'identifiant du personnage et passe le JWT dans l'URL pour se connecter : `ws://[host]/ws/{session_id}/{character_id}?token={token}`.
