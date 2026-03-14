#!/bin/bash
echo "Starting FastAPI Server..."
# Naviguer dans le dossier src pour éviter les problèmes d'import (si nécessaire, bien que module run marche aussi)
# ou exécuter uvicorn depuis le dossier racine du projet
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
