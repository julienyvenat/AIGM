# AIGM
Artificial Intelligence Game Master for RPG

## Installation et lancement du Backend

```bash
cd backend
pip install -r requirements.txt
python -m src.scripts.seed_data
cd ..
backend/run.sh
```

## Installation et lancement du Frontend

```bash
cd frontend
yarn install
yarn dev
```

Modifier le `frontend/.env` afin d'y insérer le bon nom de domaine du backend.

Coper le fichier `backend/.env.exemple` vers `backend/.env` et renseignez les variables.