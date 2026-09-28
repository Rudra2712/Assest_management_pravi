# R&B Immovable Physical Asset Inventory & Lifecycle Management System

A centralized, GIS-enabled system for the Roads & Buildings (R&B) Department to inventory, inspect,
maintain and manage **non-movable physical infrastructure assets** — roads, bridges, culverts,
government buildings and other fixed structures — across their complete lifecycle.

This is a hackathon MVP: a single FastAPI backend, a single React frontend, and PostgreSQL.
No Docker, no Nginx, no Redis/Celery, no MinIO — everything runs with two commands on a normal
developer machine.

## Architecture

```
Browser
   |
   v
React + Vite + Tailwind (GIS map, dashboards)
   |  REST (fetch/axios)
   v
FastAPI (single modular app: auth, assets, GIS, lifecycle, inspections,
         maintenance, projects, documents, audit)
   |
   +--> PostgreSQL             (relational data + GeoJSON geometry)
   +--> backend/uploads/       (local document storage; S3-ready abstraction)
```

See [docs/architecture.md](docs/architecture.md) for details, [docs/database.md](docs/database.md) for
the schema/ERD, and [docs/api.md](docs/api.md) for the API surface.

## Prerequisites

1. **Node.js** 18+ and npm
2. **Python** 3.11+
3. **PostgreSQL** 14+ (no PostGIS extension required)

## Setup (Windows)

### 1. Create the database

As the `postgres` superuser (adjust the path to your PostgreSQL `bin` directory):

```bash
"C:\Program Files\PostgreSQL\<version>\bin\psql.exe" -U postgres -f scripts\setup_local_db.sql
```

This creates the `rb_admin` role and the `rb_assets` database.

### 2. Configure environment

```bash
copy .env.example .env
```

The defaults in `.env.example` match `scripts\setup_local_db.sql` (`rb_admin` / `rb_dev_password` /
`rb_assets` on `localhost:5432`) — edit `DATABASE_URL` if your local setup differs.

### 3. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m seed.seed_data
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000` (interactive API docs at `http://localhost:8000/docs`).

### 4. Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` and talks directly to the backend at `http://localhost:8000`.

### 5. Log in

Use any of the seeded demo accounts (password `Password123!` for all):

| Email | Role |
|---|---|
| state.admin@rnb.gov.in | State Administrator |
| dept.admin@rnb.gov.in | R&B Department Administrator |
| field.engineer@rnb.gov.in | Field Engineer / Inspector |
| maintenance.officer@rnb.gov.in | Maintenance Officer |
| contractor.user@rnb.gov.in | Contractor |

All seed data (assets, users, inspections, work orders, projects) is **synthetic demo data** and
does not represent real government records.

## Deploying to Vercel

See [docs/deployment.md](docs/deployment.md) — two Vercel projects (frontend + backend) plus a
free Neon Postgres database, with the real tradeoffs of running this on serverless (document
uploads need external storage in production) spelled out up front.

## Running tests

```bash
cd backend
venv\Scripts\activate
pytest
```

Some tests require the local PostgreSQL database configured above; the lifecycle and
condition-scoring services also have pure unit tests that run without a database.

## Project layout

```
/
  backend/
    app/            FastAPI app: routers, models, schemas, services, auth, permissions, gis, utils
    migrations/      Alembic migrations
    seed/            Demo data seed script
    tests/           Pytest suite
    uploads/         Local document storage (gitignored contents)
  frontend/
    src/
      pages/         Route-level screens
      components/    Shared UI components
      layouts/       App shell / navigation
      api/           Typed API client functions (axios)
      hooks/         Auth context, etc.
      types/         Shared TypeScript types
      routes/        Route guards
  docs/              Architecture, database, API, setup, security docs
  scripts/           One-off setup scripts (local DB bootstrap)
```

## What's implemented (MVP scope)

Authentication + RBAC + jurisdiction scoping, administrative hierarchy, asset registry with
type-specific detail (roads/bridges/culverts/buildings/structures), GeoJSON-backed GIS map with
filtering, an auditable lifecycle state machine, the full inspection workflow (assign → GPS →
checklist → findings → photos → submit → supervisor review), deterministic/explainable condition
& risk scoring, maintenance requests → approval → work orders → contractor assignment →
completion → verification, projects linked to assets, contractors, document upload/versioning on
local disk, dashboards (state + GIS + field), audit logs, and CSV asset import with duplicate
detection.

Notifications, email/SMS and government SSO are stubbed/future-scope per the original spec —
see `docs/architecture.md` for what's deliberately out of scope for this MVP.
