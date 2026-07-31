FROM python:3.12-slim-bookworm

WORKDIR /app

# psycopg2 needs these to build against the system Postgres client library.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Most hosts (Railway, Render, Fly.io) inject $PORT at runtime; 8000 is the
# local fallback so `docker run -p 8000:8000 ...` still works unmodified.
ENV PORT=8000
EXPOSE 8000

# Run migrations, then start the server. If migrations fail, the container
# fails fast instead of serving with a stale or missing schema.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
