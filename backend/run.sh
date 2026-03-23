#!/bin/bash
cd "$(dirname "$0")"
echo "Starting FastAPI Server..."
# Naviguer dans le dossier src pour éviter les problèmes d'import (si nécessaire, bien que module run marche aussi)
# ou exécuter uvicorn depuis le dossier racine du projet
uvicorn main:app --app-dir src --host 0.0.0.0 --port 8000 --reload
