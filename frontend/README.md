# Arnav LMS — Frontend

React frontend for the Arnav LMS API. Covers both the admin portal and the
student learning experience, with role-aware routing driven by the `role` field
returned by `/auth/me`.

## Running it

```bash
npm install
cp .env.example .env      # then point VITE_API_BASE_URL at your API
npm run dev               # http://localhost:5173
```

The backend's CORS list already allows `http://localhost:5173`, so no backend
change is needed for local development.

```bash
npm run build             # production bundle in dist/
npm run preview           # serve the built bundle locally
```

## Tests

```bash
npm test                  # once
npm run test:watch        # while working
```

Vitest with React Testing Library, driving components the way a person
uses them — click the option, press submit — rather than reaching into
component state. The API layer is mocked at `src/api/endpoints`, so these
cover the UI's own behaviour and the backend suite covers the rest.

Worth knowing what they are protecting:

- **`CourseBuilder.test.jsx`** is the client half of a data-integrity
  guarantee. The API matches chapters and lessons by `id`; if the builder
  stops sending them, a save reads as "delete everything and create new
  rows" and every student's progress against that course is destroyed.
  The backend cannot detect the difference, so this is the only thing that
  catches it.
- **`CoursePlayer.test.jsx`** covers the unlock rules and the hand-offs —
  a quiz is offered, never opened automatically; a finished course is a
  state rather than an error, even though the API reports it as a 404.
- **`AuthContext.test.jsx`** covers being signed out mid-session, which is
  reachable without a token expiring: it stops working the moment an admin
  resets that account's password or changes its role.


## Configuration

| Variable | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Base URL of the FastAPI backend, without a trailing slash. |

Vite inlines this at build time, so a change requires a rebuild, not just a restart.

## Structure

```text
src/
├── api/
│   ├── client.js         fetch wrapper — JWT, base URL, ApiError, 401 handling
│   ├── endpoints.js      one function per backend route
│   ├── useAsync.js       reads: data / loading / error / reload
│   └── useMutation.js    writes: busy / error, and a double-click guard
├── auth/
│   ├── AuthContext.jsx   session state, restores token on refresh
│   └── LoginPage.jsx     sign in (there is no self-service registration)
├── components/
│   ├── ErrorBoundary.jsx catches a render crash so it is not a blank page
│   ├── Shell.jsx         sidebar and layout, role-aware navigation
│   └── ui.jsx            shared presentational pieces
├── admin/                dashboard, students, quizzes, certificates, roster
│   └── courses/          page, course builder, access matrix, detail drawer
├── student/              dashboard, course browsing, course player
├── test/                 vitest setup and a router-aware render helper
├── App.jsx               routing, guards, lazy-loaded admin pages
└── styles/               tokens.css, layout.css, components.css, responsive.css
```

Pages live under `admin/` and `student/`. Anything that outgrows a single
file gets a folder beside it — `admin/courses/` was one 594-line file
holding four separate things.

`api/useAsync` is for reads, `api/useMutation` for writes. Every page used
to hand-roll the write case, and most got the same detail wrong: clearing
the busy flag on success as well as failure, so a slow save could be
submitted twice.

Admin pages are lazily loaded in `App.jsx`. They are the bulk of the
application and most people here are students, who can never open any of
them — keeping them out of the initial download takes it from 235 kB to
205 kB.

## How the API client works

`src/api/client.js` owns three concerns:

- **Base URL** — read once from `VITE_API_BASE_URL`, trailing slash stripped.
- **Token** — stored in `localStorage` under `arnav.token`, attached as
  `Authorization: Bearer <token>` on every authenticated request.
- **Errors** — any non-2xx response raises an `ApiError` carrying `status` and
  `detail`. FastAPI's 422 validation arrays are flattened into a readable
  sentence. Convenience getters (`isNotFound`, `isForbidden`, `isUnauthorised`)
  let views branch on status without magic numbers.

`src/api/endpoints.js` maps one function to each backend route, so no component
ever builds a URL by hand.

## Endpoint coverage

| Area | Endpoint | Used by |
| --- | --- | --- |
| Auth | `POST /auth/login` | Login |
| Auth | `GET /auth/me` | Session restore |
| Courses | `GET /courses` | Admin courses, student courses, player |
| Courses | `POST /courses/{id}/publish` | Admin courses |
| Courses | `POST /courses/{id}/archive` | Admin courses |
| Chapters | `GET /courses/{id}/chapters` | Course player, course builder |
| Builder | `POST /admin/courses` | Admin courses |
| Builder | `PUT /admin/courses/{id}` | Admin courses |
| Builder | `DELETE /admin/courses/{id}` | Admin courses |
| Access | `GET /admin/courses/{id}/access` | Access grid |
| Access | `POST /admin/courses/{id}/access` | Access grid |
| Access | `DELETE /admin/courses/{id}/access` | Access grid |
| Admin | `GET /admin/dashboard` | Admin dashboard |
| Admin | `GET /admin/departments` | Reference data cache (`api/referenceData.js`) |
| Admin | `GET /admin/roles` | Reference data cache (`api/referenceData.js`) |
| Admin | `GET /admin/students` | Admin students |
| Admin | `GET /admin/students/{id}/progress` | Student drawer |
| Admin | `GET /admin/courses/{id}/students` | Course roster |
| Admin | `PATCH /admin/users/{id}` | Student editor |
| Learning | `GET /learning/courses/{id}/continue` | Course player |
| Learning | `GET /learning/courses/{id}/progress` | Course player |
| Progress | `POST /progress/complete` | Course player |
| Student | `GET /me/dashboard` | Student dashboard, course list |

Not yet wired: `GET /courses/{id}/chapters/{chapterId}`, `GET /progress/me`.

Department and seniority lists are fetched once per session from
`GET /admin/departments` and `GET /admin/roles` (both open to any signed-in
user, not just admins, since every account needs to resolve its own
department label) and cached in `api/referenceData.js`. Add a value in
`app/constants.py` and it shows up everywhere without a frontend change.

## Backend details the client depends on

A few of these are easy to break accidentally:

- **Login is form-encoded, not JSON.** `OAuth2PasswordRequestForm` expects
  `application/x-www-form-urlencoded`, and the email goes in the `username`
  field.
- **No route uses a trailing slash.** A mismatch causes a 307 redirect that
  drops the `Authorization` header.
- **Revoking access is a `DELETE` with a JSON body**, matching
  `GrantAccessRequest`.
- **`/learning/courses/{id}/continue` returns 404 once a course is finished.**
  The player treats that as a completed state, not an error.
- **There is no `GET /courses/{id}`.** Single-course details are found by
  filtering the list response.

## Behaviour worth knowing

- **Sequence locking** is enforced by the backend and reflected in the UI:
  locked subchapters render disabled in the contents rail, and
  `POST /progress/complete` is refused server-side if attempted out of order.
- **Students with no access profile** see a prompt to contact their
  administrator rather than an empty screen.
- **Admins bypass access rules** on the backend, so the admin course list shows
  every course including drafts and archived ones.

## Design

- **Headings** — Cinzel, chosen to echo the carved, wide-tracked serif of the
  ARNAV wordmark.
- **Body** — Source Serif 4.
- **Interface text** — Inter, keeping dense tables legible.
- **Palette** — ivory `#EFEAE4`, parchment `#E3D8CC`, champagne `#E6D3A3`,
  gold `#C9A13B`, bronze `#6B4F3A`, ink `#0F0F0F`, charcoal `#2A2A2A`,
  slate `#AFAFB4`, stone `#8C8C8C`.

Fonts load from Google Fonts in `index.html`. To self-host them, download the
families and replace that `<link>` with local `@font-face` rules.

## Deployment

`npm run build` produces a static bundle in `dist/`. Host it anywhere static —
Vercel, Netlify, S3, or Nginx.

Two things to remember when you deploy:

1. Set `VITE_API_BASE_URL` to the production API URL **before** building.
2. Add the frontend's production origin to `allow_origins` in `app/main.py`.

Because this uses client-side routing, configure the host to rewrite unknown
paths to `index.html`, or a refresh on `/admin/courses` will return a 404.
