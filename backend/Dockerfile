# AIGM backend -- FastAPI/SQLModel API + WebSocket server.
#
# Runs from a `backend/` working directory inside the image, matching the
# existing dev convention (backend/run.sh does `cd backend && uvicorn
# src.main:app`) -- main.py mounts /images and /audio at the *relative*
# paths "backend/images"/"backend/audio", so preserving the same CWD here
# avoids changing that (pre-existing, out of scope for Phase E) behavior.
FROM python:3.11-slim AS base

# Runtime deps for asyncpg/psycopg-style builds and bcrypt/cryptography
# wheels that occasionally need a compiler on slim images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./

# Persistent app data (SQLite fallback DB, generated images/audio, ChromaDB
# RAG store) -- mounted as volumes in docker-compose.prod.yml so they
# survive container recreation.
RUN mkdir -p backend/images backend/audio /app/chroma_data

EXPOSE 8000

# Run Alembic migrations, then start uvicorn. A single worker by default:
# the WebSocket ConnectionManager and the ChromaDB client in
# src/memory/vector_db.py both hold in-process state (see the multi-worker
# note in DEPLOY.md / the Phase E report) and are not safe to run behind
# more than one worker process without further changes. UVICORN_WORKERS is
# still exposed as an env var for anyone who wants to override this after
# addressing that, but the safe, correct default for this small
# single-NAS/small-group deployment is 1.
ENV UVICORN_WORKERS=1
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS}"]
