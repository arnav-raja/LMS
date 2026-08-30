# Deploying Arnav LMS

This puts both halves of the system on the real internet, so people other
than you can use it.

You will end up with three things, all free at the size of a small team:

- A cloud database (replacing the Postgres on your computer)
- The backend, running on Render
- The frontend, running on Vercel

> **Everything lives in one repository.**
> `backend/` and `frontend/` are both inside
> `github.com/arnav-raja/LMS`. This matters: both Render and Vercel need
> to be told **which folder** to build. That setting is called **Root
> Directory**, and getting it wrong is the most common reason a deploy
> fails or silently serves the wrong thing.
>
> An older version of this guide told you to create two separate
> repositories. That is out of date. Ignore any instruction to run
> `git init` or make a new repo — your code is already on GitHub.

Replace anything written like `<your-...>` with your own value.

## Part 1 — A Cloud Database

The Postgres on your computer only exists there, so a live website cannot
reach it.

1. Go to **neon.tech** and sign up
2. Create a project — call it anything, e.g. `arnav-learning`
3. Copy the **connection string** (it starts with `postgresql://`)
4. Keep it safe — you will paste it in below

You do not need to create any tables by hand. The migration files build
them on first deploy.

## Part 2 — Deploy The Backend (Render)

Render runs the Python app. Free tier, no card needed.

1. On **render.com**, click **New** → **Web Service**
2. Connect GitHub and pick the **`LMS`** repository
3. Fill in:
   - **Root Directory:** `backend` ← **this one matters most**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:**
     `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add:

   ```
   DATABASE_URL=<your Neon connection string>
   SECRET_KEY=<a long random string>
   ACCESS_TOKEN_EXPIRE_MINUTES=480
   ALLOWED_ORIGINS=http://localhost:5173
   ```

   `ALLOWED_ORIGINS` is a placeholder for now. Part 4 replaces it with the
   real frontend address.

   Two optional ones:

   ```
   ALGORITHM=HS256      # this is the default; only set it to change it
   LOG_LEVEL=INFO       # WARNING logs problems only
   ```

5. Click **Create Web Service**

### Check it worked

Open `https://<your-render-url>/health`. You want:

```json
{"status": "running", "database": "ok"}
```

If you get **503** with `"database": "unreachable"`, the app started but
cannot reach Neon. Check `DATABASE_URL`.

If the deploy **failed** instead, read the log for the `alembic` step —
see "When a deploy fails" at the bottom.

### The free tier sleeps

Render's free services sleep after 15 minutes with no traffic, and take
30–60 seconds to wake up. The first request after a quiet period looks
broken but is not.

## Part 3 — Deploy The Frontend (Vercel)

**Same repository.** You do not push the frontend anywhere separate.

1. Go to **vercel.com** → **Add New** → **Project**
2. Import the **same `LMS`** repository
3. Set:
   - **Root Directory:** `frontend` ← **required, or the build fails**
   - Framework preset: **Vite** (Vercel usually detects this)
4. Under **Environment Variables**, add:

   ```
   VITE_API_BASE_URL=https://<your-render-url>
   ```

   No slash on the end. Use the real Render address from Part 2.
5. Click **Deploy**

`frontend/vercel.json` already tells Vercel to send every route back to
`index.html`, so refreshing on `/admin/courses` will not 404.

## Part 4 — Let Them Talk To Each Other

The backend currently only trusts `localhost`. Go back to Render:

1. Open the service → **Environment**
2. Change `ALLOWED_ORIGINS` to your real Vercel address:

   ```
   ALLOWED_ORIGINS=https://<your-vercel-url>
   ```

3. Save. Render redeploys on its own.

Now open your Vercel address. You should see the ARNAV login screen.

If the page loads but signing in does nothing, open the browser console.
A CORS error means `ALLOWED_ORIGINS` does not exactly match your Vercel
address — check for a missing `https://` or a trailing slash.

## Part 5 — Create Your First Admin

There is no sign-up page. The first admin is made by hand.

`create_admin.py` uses whatever `DATABASE_URL` your **local** `.env`
points at. To point it at the live database:

1. Edit your local `.env` and put the Neon connection string in
   `DATABASE_URL`
2. Run:

   ```bash
   python create_admin.py
   ```

3. Follow the prompts
4. **Put your local `DATABASE_URL` back** afterwards

The password must be at least 10 characters and not an obvious one. The
script will tell you if it is not good enough.

## Deploying changes after the first time

Both services watch the same repository. A push to `main` can trigger
both.

**Deploy the two halves together.** They are not independent. The course
builder sends an `id` for every chapter and lesson so the API knows a
reordered chapter is the same chapter. An old frontend against a new
backend sends no ids, and a course save would then be read as "delete
everything and make new rows" — which destroys students' progress.

If they do land separately, new-frontend-against-old-backend is the safe
direction: the old backend just ignores the ids. Avoid editing a course
until both are green.

Two more things to expect on a deploy that includes backend changes:

- **Everyone gets signed out once.** Sign-in tokens carry a version
  number. A change to that version makes older tokens stop working, which
  is exactly what should happen when someone's password or role changes.
- **`VITE_API_BASE_URL` is baked in at build time.** Changing it in
  Vercel's settings does nothing until you redeploy.

## When a deploy fails

Almost always one of these:

**"relation ... does not exist" / the app starts then 500s**
Migrations did not run. Check the Start Command still begins with
`alembic upgrade head`.

**A migration fails on a CHECK constraint**
The database holds a value the app never writes. Find it:

```sql
SELECT DISTINCT role FROM users;
SELECT DISTINCT status FROM courses;
```

Roles must be `admin` or `student`. Statuses must be `draft`,
`published` or `archived`. Fix the odd rows, then redeploy.

**`SECRET_KEY is not set` at startup**
The app refuses to start without it, on purpose. Set it in Render.

**Vercel builds nothing, or 404s on every page**
**Root Directory** is not set to `frontend`.

**Render cannot find `requirements.txt`**
**Root Directory** is not set to `backend`.

## Finding a problem after it is live

Every response carries an `X-Request-ID` header, and a 500 shows that id
on screen. Search your Render logs for it and you will find every line
that request produced, including the full error.

Logs are one JSON line each, so you can search them properly.

## Cost

Neon, Render and Vercel all have a genuinely free tier that suits a small
team's internal training system. None of this needs payment to start.
