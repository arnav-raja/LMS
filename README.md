# Arnav LMS

A Learning Management System for internal corporate training: course
authoring, chapter/quiz content, progress tracking, automatic certificate
issuance, and department/seniority-based access control.

This top-level folder holds two independent projects, each with its own git
history, meant to be deployed separately:

- [`LearningSystemBackend/`](LearningSystemBackend) — FastAPI + PostgreSQL API.
  See [its README](LearningSystemBackend/README.md) for setup, and
  [DEPLOYMENT.md](LearningSystemBackend/DEPLOYMENT.md) for the full
  production deployment guide.
- [`LearningSystemFrontend/`](LearningSystemFrontend) — React + Vite client.
  See [its README](LearningSystemFrontend/README.md) for setup and how it
  talks to the API.

## Running both locally

```bash
# Terminal 1 — backend (http://localhost:8000)
cd LearningSystemBackend
docker compose up --build

# Terminal 2 — frontend (http://localhost:5173)
cd LearningSystemFrontend
npm install
cp .env.example .env
npm run dev
```

The backend's default `ALLOWED_ORIGINS` already includes
`http://localhost:5173`, and the frontend's default `VITE_API_BASE_URL`
already points at `http://localhost:8000`, so no configuration is needed for
local development.

Once both are running, create the first admin account — see "Running it
locally" in [the backend README](LearningSystemBackend/README.md) for the
`create_admin.py` setup needed when using Docker Compose.

There is no self-service registration — every other account is created by an
admin from the Students page in the app.
