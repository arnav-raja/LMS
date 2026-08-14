# Deploying Arnav LMS

This walks through putting both halves of the system on the real internet, so
people other than you can use it. It assumes you've already got everything
running locally on your own machine (if not, do that first — deploying a
system you haven't tested yourself just moves the debugging online).

You'll end up with three things, all free at the scale of a small team:

- A cloud database (replacing your local Postgres)
- The backend, running on a hosting service
- The frontend, running on a hosting service

## Part 1 — A Cloud Database

Your local Postgres only exists on your computer, so a live website can't
reach it. We'll move to a free hosted database instead.

1. Go to **neon.tech** and sign up
2. Create a new project — call it anything, e.g. `arnav-learning`
3. Copy the **connection string** it gives you (starts with `postgresql://`)
4. Keep it somewhere safe — you'll paste it in twice below

This replaces the `DATABASE_URL` you've been using locally. Your existing
tables don't need to be recreated by hand — the migration files will build
them fresh on this new database in Part 2.

## Part 2 — Deploy The Backend

We'll use **Render** (render.com) — free tier, no credit card needed, and it
runs a plain Python app directly without needing Docker.

### Get your code onto GitHub

Render deploys from a GitHub repository, not a zip file.

1. Go to **github.com**, sign up if you haven't already
2. Click the **+** in the top right → **New repository** → name it
   `learning-system-backend` → **Create repository**
3. On your own computer, inside the `LearningSystem` folder, run:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/learning-system-backend.git
   git push -u origin main
   ```
   (Replace `YOUR-USERNAME` with your actual GitHub username. If `git` isn't
   recognised, install it from **git-scm.com** first.)

Your `.env` file will **not** be uploaded — `.gitignore` already excludes it,
which is correct, since it holds your real password.

### Create the Render service

1. On Render, click **New** → **Web Service**
2. Connect your GitHub account, pick `learning-system-backend`
3. Fill in:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Under **Environment Variables**, add each of these (values from your Neon
   connection string and your own choices):
   ```
   DATABASE_URL=<your Neon connection string>
   SECRET_KEY=<a long random string>
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=480
   ALLOWED_ORIGINS=http://localhost:5173
   ```
   (We'll update `ALLOWED_ORIGINS` again once the frontend has a real URL —
   for now this placeholder just lets the build succeed.)
5. Click **Create Web Service**

Render will build and start it. Once it says **Live**, you'll have a real URL
like `https://learning-system-backend.onrender.com`. Visit
`https://your-url.onrender.com/docs` to confirm it's alive, exactly like you
did with `localhost:8000/docs` earlier.

**Free-tier note:** Render's free web services sleep after 15 minutes of no
traffic, and take 30–60 seconds to wake back up on the next request. That's
normal, not a bug — worth knowing so the first request after a quiet period
doesn't look broken.

## Part 3 — Deploy The Frontend

We'll use **Vercel** (vercel.com) — same GitHub-based flow.

1. Push the frontend folder to a second GitHub repository the same way as
   above (`learning-system-frontend`)
2. Go to **vercel.com**, sign up, click **Add New** → **Project**
3. Import `learning-system-frontend`
4. Under **Environment Variables**, add:
   ```
   VITE_API_BASE_URL=https://learning-system-backend.onrender.com
   ```
   (use your actual Render URL from Part 2)
5. Click **Deploy**

Once it finishes, you'll get a URL like
`https://learning-system-frontend.vercel.app`.

The `vercel.json` file already in the project tells Vercel to send every
route back to `index.html`, so refreshing on `/admin/courses` won't 404 —
this is the client-side routing fix mentioned in the README.

## Part 4 — Connect Them For Real

Right now the backend only trusts `localhost:5173`. Go back to Render:

1. Open your web service → **Environment**
2. Update `ALLOWED_ORIGINS` to your real Vercel URL:
   ```
   ALLOWED_ORIGINS=https://learning-system-frontend.vercel.app
   ```
3. Save — Render redeploys automatically

Visit your Vercel URL. You should see the ARNAV login screen, now genuinely
live on the internet.

## Part 5 — Create Your First Admin, In Production

`create_admin.py` runs against whatever `DATABASE_URL` your **local** `.env`
points to. To use it against your live database:

1. Temporarily edit your local `.env`, replacing `DATABASE_URL` with your
   Neon connection string (the same one Render is using)
2. Run:
   ```
   python create_admin.py
   ```
3. Follow the prompts to create your production admin account
4. **Change `DATABASE_URL` back** to your local Postgres string afterwards,
   so your local development environment still points at your own machine

## Keeping Both In Sync Going Forward

- **Backend code changes:** `git push` to the backend repository — Render
  redeploys automatically.
- **Frontend code changes:** `git push` to the frontend repository — Vercel
  redeploys automatically.
- **Changing `VITE_API_BASE_URL`:** Vite bakes this in at build time, so
  after changing it in Vercel's settings, trigger a new deploy (Vercel does
  this automatically on the next push, or you can click **Redeploy** in the
  dashboard).

## A Note On Cost

Everything above — Neon, Render, Vercel — has a genuinely free tier suitable
for a small team's internal training system. If usage grows significantly,
each has a paid tier with more capacity, but none of this requires paying
anything to get started.
