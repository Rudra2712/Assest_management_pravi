# Setup

See the root [README.md](../README.md) for the full step-by-step (Windows-focused) setup. Summary:

1. Install Node.js 18+, Python 3.11+, PostgreSQL 14+ with PostGIS.
2. `psql -U postgres -f scripts\setup_local_db.sql` — creates the `rb_admin` role, `rb_assets`
   database, and enables PostGIS.
3. `copy .env.example .env`
4. Backend: `cd backend && python -m venv venv && venv\Scripts\activate && pip install -r
   requirements.txt && alembic upgrade head && python -m seed.seed_data && uvicorn app.main:app
   --reload`
5. Frontend: `cd frontend && npm install && npm run dev`
6. Open `http://localhost:5173` and log in with a seeded demo account (see README).

No Docker, Nginx, Redis or MinIO required — the frontend talks to the backend directly, and files
are stored under `backend/uploads/`.

## Troubleshooting

- **`password authentication failed for user "rb_admin"`** — rerun
  `psql -U postgres -f scripts\setup_local_db.sql` to reset the local role password to
  `rb_dev_password`, which matches the default `DATABASE_URL`. If your PostgreSQL credentials
  differ, update `DATABASE_URL` in the backend environment instead.
- **`psql: command not found`** — use the full path to `psql.exe` under your PostgreSQL
  installation's `bin` directory, or add it to `PATH`.
- **`CREATE EXTENSION postgis` fails** — PostGIS isn't installed for your PostgreSQL version yet.
  On Windows, re-run the PostgreSQL installer and choose "Stack Builder" → Spatial Extensions →
  PostGIS, or download the matching PostGIS bundle from postgis.net.
- **CORS errors in the browser** — confirm `BACKEND_CORS_ORIGINS` in `.env` includes
  `http://localhost:5173` (the default) and that you restarted `uvicorn` after editing `.env`.
- **File uploads fail** — the backend creates `backend/uploads/` automatically on startup; confirm
  the process has write permission to that folder.
