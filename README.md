# Arnav LMS — Backend

A Web-Based Learning Management System API built using FastAPI and PostgreSQL.

## Features

- JWT authentication (no self-service registration — every account is
  created by an administrator)
- Course, chapter, and subchapter management
- Mandatory per-chapter quizzes
- Learning progress tracking, with server-enforced sequencing
- Automatic certificate issuance on course completion, downloadable as a
  branded PDF or image
- Department/seniority-based course access rules
- Admin dashboard and student roster views

## Technology Stack

- Python, FastAPI
- PostgreSQL, SQLAlchemy, Alembic
- JWT (python-jose), bcrypt (passlib)

## Running it locally

**Option 1 — Docker Compose** (Postgres + API in one command):

```bash
docker compose up --build
```

This starts Postgres, runs migrations, and serves the API at
`http://localhost:8000`.

**Option 2 — a local Python environment:**

```bash
python -m venv venv
venv\Scripts\activate       # or: source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env        # then point DATABASE_URL at your own Postgres
alembic upgrade head
uvicorn app.main:app --reload
```

Either way, create the first admin account against whichever database you
just set up. `create_admin.py` runs on the host and reads `DATABASE_URL` from
`.env`, so with Docker Compose your `.env` needs to point at the exposed
port instead of the `db` service name:

```bash
# .env, when the database is the one started by docker compose
DATABASE_URL=postgresql://learning_system:learning_system@localhost:5432/learning_system
```

```bash
pip install -r requirements.txt   # create_admin.py needs the app's dependencies
python create_admin.py
```

Interactive API docs are available at `/docs` once the server is running.

## Tests

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Tests run against an in-memory SQLite database and never touch the database
configured in `.env`.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full free-tier deployment guide
(Neon + Render + Vercel).
