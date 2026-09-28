# Deploying to Vercel

This deploys as **two separate Vercel projects** pointed at the same GitHub repo — one for
`frontend/` (a static Vite build), one for `backend/` (FastAPI as Python serverless functions).
Vercel doesn't host PostgreSQL, so the database lives on **Neon** (serverless Postgres — the same
engine Vercel's own "Vercel Postgres" product is built on, generous free tier, no PostGIS needed
since geometry is stored as plain JSONB in this app).

## Read this before you deploy: the tradeoffs

Moving from local dev to Vercel serverless changes two things about how the app behaves. Neither
is fixed by this config — they're architectural consequences of "serverless" that are worth
deciding on deliberately:

1. **Document uploads won't persist.** `backend/app/utils/storage.py` writes to local disk.
   Vercel functions get a fresh, read-only filesystem per invocation except `/tmp`, which is
   writable but wiped between cold starts and never shared across instances. In production, a
   file uploaded in one request will very likely be gone by the time a later request tries to
   download it. `app/config.py` already redirects `UPLOAD_DIR` to `/tmp` on Vercel so the app
   doesn't crash — but this is a demo-safe workaround, not a fix. The real fix is swapping
   `app/utils/storage.py` for an S3-compatible backend (Vercel Blob, Cloudflare R2, AWS S3) — the
   module is deliberately the only place that touches the filesystem so that swap doesn't touch
   any router. Not done here because it wasn't asked for; flagging it so it doesn't surprise you.
2. **Cold starts + connection limits.** Every serverless invocation can be a new process. The
   backend already uses `NullPool` on Vercel (`app/database.py`) so it doesn't leak pooled
   connections across invocations — but you still need Neon's **pooled** connection string
   (the one with `-pooler` in the hostname) as `DATABASE_URL` in production, or you'll exhaust
   Neon's direct connection limit under any real concurrency.

If you only need this for a demo/hackathon judging session, both are fine as-is — just don't rely
on uploaded documents surviving between visits.

## 1. Create the database (Neon)

1. Create a free project at [neon.tech](https://neon.tech).
2. Copy the **pooled** connection string (hostname contains `-pooler`), and rewrite it for
   SQLAlchemy + psycopg:
   ```
   postgresql+psycopg://<user>:<password>@<host>-pooler.neon.tech/<db>?sslmode=require
   ```
3. Apply the schema from your machine (Neon is just Postgres over the network):
   ```bash
   cd backend
   venv\Scripts\activate
   set DATABASE_URL=postgresql+psycopg://<user>:<password>@<host>-pooler.neon.tech/<db>?sslmode=require
   alembic upgrade head
   python -m seed.seed_data   # optional — loads the same synthetic demo data as local dev
   ```
   Re-run `alembic upgrade head` the same way after any future migration.

## 2. Deploy the backend

1. On [vercel.com](https://vercel.com), **Add New → Project**, import this repo.
2. Set **Root Directory** to `backend`. Vercel picks up `backend/vercel.json` and
   `backend/api/index.py` automatically (Python runtime, `@vercel/python`).
3. Environment variables (Project Settings → Environment Variables):

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | the Neon pooled connection string from step 1 |
   | `SECRET_KEY` | a fresh random string — `openssl rand -hex 32` (never reuse the `.env.example` placeholder) |
   | `BACKEND_CORS_ORIGINS` | `["https://your-frontend.vercel.app"]` — JSON array, exact string, no trailing slash |
   | `ENVIRONMENT` | `production` |

4. Deploy. Note the resulting URL, e.g. `https://your-backend.vercel.app` — the API lives under
   `https://your-backend.vercel.app/api/v1`, docs at `/docs`.

## 3. Deploy the frontend

1. **Add New → Project** again, same repo, **Root Directory** set to `frontend`.
2. Vercel auto-detects Vite; `frontend/vercel.json` adds the SPA rewrite so client-side routes
   (`/assets/:id`, `/grievances`, …) don't 404 on refresh.
3. Environment variable:

   | Variable | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://your-backend.vercel.app/api/v1` |

4. Deploy. Then go back to the **backend** project's `BACKEND_CORS_ORIGINS` and set it to this
   frontend's actual URL (chicken-and-egg: the backend needs to know the frontend's final URL,
   which only exists after this step) and redeploy the backend.

## 4. Verify

- `https://your-backend.vercel.app/health` → `{"status": "ok", ...}`
- `https://your-frontend.vercel.app/login` → log in with a seeded demo account
- If login fails with a network/CORS error in the browser console, double-check
  `BACKEND_CORS_ORIGINS` matches the frontend URL **exactly** (scheme + host, no path, no
  trailing slash) and that you redeployed the backend after changing it.

## Local development is unaffected

Everything above is additive — `IS_SERVERLESS` in `app/config.py` only activates when Vercel sets
its own `VERCEL=1` environment variable, so `uvicorn app.main:app --reload` locally still uses
`backend/uploads/` and a normal connection pool exactly as before. See the root
[README.md](../README.md) for local setup.
