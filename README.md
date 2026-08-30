# Arnav LMS

A Learning Management System for internal corporate training: course
authoring, chapter/quiz content, progress tracking, automatic certificate
issuance, and department/seniority-based access control.

Two projects, deployed separately:

- [`backend/`](backend) — FastAPI + PostgreSQL API. See
  [its README](backend/README.md) for setup, and
  [DEPLOYMENT.md](backend/DEPLOYMENT.md) for the production guide.
- [`frontend/`](frontend) — React + Vite client. See
  [its README](frontend/README.md) for setup and how it talks to the API.

## Running both locally

```bash
# Terminal 1 — backend (http://localhost:8000)
cd backend
docker compose up --build

# Terminal 2 — frontend (http://localhost:5173)
cd frontend
npm install
cp .env.example .env
npm run dev
```

The backend's default `ALLOWED_ORIGINS` already includes
`http://localhost:5173`, and the frontend's default `VITE_API_BASE_URL`
already points at `http://localhost:8000`, so no configuration is needed
for local development.

Once both are running, create the first admin account — see "Running it
locally" in [the backend README](backend/README.md) for the
`create_admin.py` step needed when using Docker Compose.

There is no self-service registration. Every other account is created by
an admin from the Students page in the app.

## Tests

```bash
# Backend — needs a throwaway PostgreSQL; see backend/README.md
cd backend
docker compose --profile test up -d test-db
pytest

# Frontend
cd frontend
npm test
```

Both run in CI on every push and pull request
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

## How the pieces fit

A **course** holds ordered **chapters**, each holding ordered
**subchapters** (lessons) and at most one **quiz**.

Who can see a course is not an enrolment list. A **course access rule**
maps a course to a `(department, seniority)` pair, and a student sees a
course only when their own pair matches a rule *and* the course is
published.

Three rules gate a student's way through, and they interlock:

1. A lesson unlocks only once the previous one is complete. A locked
   lesson's text is withheld by the API, not merely hidden by the UI.
2. A chapter's first lesson also stays locked until the previous
   chapter's quiz has been passed. Chapters without a quiz never gate.
3. A certificate is issued automatically the moment every lesson is done
   and every quiz passed — there is no admin action that grants one.
   Because a course can finish on either a lesson or a quiz, that check
   runs after both.

## Things worth knowing before changing anything

- **Editing content preserves progress; deleting it does not.** The course
  and quiz builders match by `id`, so a reorder keeps every student's
  history attached — and that depends on the *client* sending those ids.
  See "Editing content without destroying progress" in the backend README.
- **Deleting an account is destructive** and takes its certificates with
  it. The endpoint reports what went, and the action is recorded in the
  audit log.
- **Tests run against real PostgreSQL**, not SQLite, because SQLite does
  not enforce foreign keys and has no `timestamptz` — both of which this
  schema depends on.
- **`tests/test_migrations.py`** fails if a model is changed without a
  migration. Nothing else would notice.
