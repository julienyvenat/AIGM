# AIGM
Artificial Intelligence Game Master for RPG

## Installation et lancement du Backend

```bash
cd backend
pip install -r requirements.txt
python -m src.scripts.seed_data
uvicorn src.main:app --reload
```

## Installation et lancement du Frontend

```bash
cd frontend
yarn install
yarn dev
```

