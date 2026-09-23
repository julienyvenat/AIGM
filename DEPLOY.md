# Déploiement AIGM (production, NAS auto-hébergé)

Déploiement pour un petit groupe privé (le propriétaire + ses joueurs), auto-hébergé
sur le NAS existant derrière Traefik, à coût d'infra récurrent nul.

- Frontend : `https://jdr.yvenat.eu`
- Backend (API + WebSocket) : `https://api.jdr.yvenat.eu`
- CI GitHub Actions build et pousse les images vers GHCR à chaque merge sur
  `main`. **Le déploiement lui-même est manuel** : aucun runner auto-hébergé,
  aucun déclenchement automatique -- voir `.github/workflows/ci.yml` et la
  note de sécurité dans ce fichier.

## Prérequis (déjà en place, rien à faire)

- Traefik tourne déjà sur le NAS (`/home/julieny/docker/docker-compose.yml`,
  non touché par ce projet) et écoute sur 80/443.
- Le réseau Docker externe `net-multimedia` existe déjà (utilisé par les
  autres services Traefik). `docker-compose.prod.yml` le déclare en
  `external: true` -- il ne le crée pas.
- Les enregistrements DNS pour `jdr.yvenat.eu` / `api.jdr.yvenat.eu` sont
  gérés séparément par le propriétaire.

## Installation initiale (une seule fois)

```bash
# Depuis la racine du repo, sur le NAS
cp .env.production.example .env.production
# Éditer .env.production : SECRET_KEY, POSTGRES_PASSWORD, OPENAI_API_KEY,
# CORS_ORIGINS, etc. -- voir les commentaires dans le fichier.
# Générer des secrets avec : openssl rand -hex 32

docker compose -f docker-compose.prod.yml up -d
```

Au premier démarrage, le service `backend` exécute automatiquement les
migrations Alembic (`alembic upgrade head`) avant de lancer uvicorn -- pas
d'étape manuelle de migration nécessaire, ni au premier déploiement ni aux
suivants.

Vérifier que tout tourne :

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend
```

## Déployer une mise à jour

CI a déjà construit et poussé les nouvelles images vers GHCR sur le dernier
merge dans `main`. Sur le NAS :

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

`up -d` relance uniquement les services dont l'image a changé ; les
migrations Alembic (via le `CMD` du conteneur backend) tournent à chaque
redémarrage du service backend -- idempotentes, donc sans risque si rien de
nouveau n'a été ajouté à `alembic/versions/`.

Pour reconstruire les images localement au lieu de les tirer de GHCR (par
exemple avant que la CI n'ait poussé une image) :

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

## Sauvegarde Postgres

Rien de sophistiqué : un `pg_dump` planifié en cron sur le NAS, en dehors des
conteneurs (le service `postgres` n'expose son port à personne d'autre que
le backend -- pas de connexion directe depuis l'hôte sans passer par
`docker exec`).

```bash
# /etc/cron.d/aigm-backup, ou crontab -e de l'utilisateur qui gère les conteneurs
0 3 * * * cd /chemin/vers/AIGM && docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U aigm aigm | gzip > /chemin/vers/backups/aigm-$(date +\%Y\%m\%d).sql.gz
```

Restauration (si besoin) :

```bash
gunzip -c /chemin/vers/backups/aigm-20260101.sql.gz | docker compose -f docker-compose.prod.yml exec -T postgres psql -U aigm aigm
```

Pensez à purger les archives anciennes (ex: garder 14 jours) dans le même
cron ou un second job -- non fait ici, volontairement minimal.

## Notes

- Les données persistantes (Postgres, images/audio générés, la base
  vectorielle ChromaDB pour le RAG) vivent dans des volumes Docker nommés
  (`aigm-postgres-data`, `aigm-backend-images`, `aigm-backend-audio`,
  `aigm-chroma-data`) -- ils survivent à un `docker compose up -d` /
  recréation de conteneur, mais pas à un `docker volume rm`.
- Le backend tourne avec un seul worker uvicorn par défaut
  (`UVICORN_WORKERS=1` dans `backend/Dockerfile`). Voir le rapport de la
  Phase E pour la limitation connue (le `ConnectionManager` WebSocket et le
  client ChromaDB sont un état en mémoire par processus, non partagé entre
  workers) -- ne pas augmenter ce nombre sans corriger ça d'abord.
