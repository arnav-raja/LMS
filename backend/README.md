# Arnav LMS — Backend

A Web-Based Learning Management System API built using FastAPI and PostgreSQL.

## Features

- JWT authentication (no self-service registration — every account is
  created by an administrator)
- Course, chapter, and subchapter management
- Mandatory per-chapter quizzes
- Learning progress tracking, with server-enforced sequencing
- Automatic certificate issuance on course completion
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
docker compose --profile test up -d test-db      # PostgreSQL on port 55432
pip install -r requirements.txt -r requirements-dev.txt
pytest
```

Tests run against a real PostgreSQL database, never against the one in
`.env`. `TEST_DATABASE_URL` selects it and defaults to the `test-db`
service above; the database name must contain "test", because the fixtures
drop every table.

PostgreSQL rather than SQLite because SQLite does not enforce foreign keys
unless switched on, and has no `timestamptz` — so cascades and timezone
handling would pass here and fail in production, which is exactly the class
of bug these tests exist to catch. It costs nothing: the schema is built
once per run and each test runs in a transaction that is rolled back.

The suite has two layers, and both matter:

- **`tests/`** — unit tests that call services directly. Fast, and good at
  covering business rules.
- **`tests/api/`** — route tests that drive the real app over HTTP with
  `TestClient`. These are the only tests that see the router layer, so they
  are what catch a route calling its service wrongly, a missing permission
  check, or a wrong status code.

Run one layer on its own with `pytest tests/api` or
`pytest tests --ignore=tests/api`.

Every route should have at least a success case and its failure cases
(401 without a token, 403 for the wrong role, 404 for a missing record).
When adding a route, add its tests in `tests/api/` in the same change.

`tests/test_migrations.py` is worth knowing about: it runs the whole
migration chain against an empty database and diffs the result against the
models. If you change a model without writing a migration, that test fails
— nothing else in the suite would notice, because the other tests build
their schema from the models directly.

## Editing content without destroying progress

The course and quiz builders both send an `id` for anything that already
exists, and `null` for anything new. That id is what identifies a chapter,
lesson, question or option across a save.

This matters more than it looks. Both builders used to match by
**position**, so reordering two chapters handed each one's completion
history to the other, and saving a quiz deleted it and built a new one,
taking every past attempt with it. Neither failed loudly; students simply
had the wrong progress, or none.

So if you touch either builder:

- keep sending the ids, on the client as well as the server — the server
  cannot tell "moved" from "replaced" without them;
- an id that does not belong to the course, chapter or quiz being edited
  is rejected, and rejected *before* anything is written, so a bad save
  leaves the content exactly as it was;
- `tests/api/test_course_builder_identity.py` and
  `tests/api/test_quiz_versioning.py` exist to hold this in place.

Deleting is different from editing, and still destructive on purpose:
deleting a course removes its content and every student's progress
against it, and deleting an account removes that person's progress,
attempts and certificates. The delete endpoint returns counts of what went
with it, and the deletion is recorded in the audit log.

## Security notes

**Sign-in is rate limited** per identifier — five failures in fifteen
minutes and that identifier is refused for the rest of the window, even
with the correct password. Attempts are counted in the `login_attempts`
table rather than in memory, so the limit survives a restart and holds
across instances. It is per identifier, not per IP, because an attacker
can change IP freely but cannot change which account they are trying to
get into; the cost is that someone else's guessing can lock a real user
out briefly, which is why the window is short.

**Access tokens carry the account's `token_version`**, and it is checked
on every request. Changing a password or a role bumps it, which makes
every token already issued to that account stop working immediately.
Without this, resetting the password of a compromised account did not
lock the intruder out — their token stayed valid until it expired on its
own, up to eight hours later.

**The token is still in `localStorage`, deliberately.** The usual argument
for moving it to an httpOnly cookie is XSS, but this frontend renders
everything through React text nodes and uses `dangerouslySetInnerHTML`
nowhere, so there is no injection point to steal it through. Moving to
cookies would also trade that for CSRF: the frontend and API are on
different sites, so the cookie would need `SameSite=None`, which is
exactly the configuration that needs CSRF tokens to be safe. Revisit this
decision if lesson content ever starts rendering as HTML — that would
introduce the XSS vector this reasoning depends on not existing.

The token payload carries only `sub`, `role` and `tv`. `role` is a
convenience for the client and is never trusted for a permission
decision: every request re-reads the account from the database.

**Passwords** must be at least 10 characters and not obviously guessable
(`app/services/password_policy.py`). The rule applies when a password is
set or changed, never to one already stored, so it does not lock existing
accounts out. Every account here is created by an admin on someone else's
behalf, which is exactly the situation that produces `Welcome123`.

**Administrative actions on accounts are recorded** in `audit_entries` —
who did it, to which account, what changed, and when. Readable at
`GET /admin/audit`, and in the app under Students → Activity. Append-only:
no route edits or removes an entry, and a password reset is recorded as
having happened without the password itself.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for the full free-tier deployment guide
(Neon + Render + Vercel).
