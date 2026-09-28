# R&B Asset Inventory

A GIS-enabled asset inventory and lifecycle management application for Roads & Buildings (R&B) teams. It brings fixed infrastructure records, field inspections, maintenance work, project tracking, and procurement workflows into one role-aware workspace.

This repository contains a React + TypeScript web app, a FastAPI REST API, and a PostgreSQL database. It is designed to run locally without Docker, PostGIS, Redis, or a separate object-storage service.

## Contents

- [What it does](#what-it-does)
- [Technology](#technology)
- [Run locally](#run-locally)
- [Demo accounts](#demo-accounts)
- [Tests and quality checks](#tests-and-quality-checks)
- [Repository map](#repository-map)
- [Documentation](#documentation)
- [Deployment and limitations](#deployment-and-limitations)

## What it does

- Maintain a searchable inventory of roads, bridges, culverts, buildings, and other fixed assets.
- View and filter asset locations on a GIS map using GeoJSON geometry and MapLibre.
- Track lifecycle transitions, inspections, condition assessments, and maintenance history.
- Route maintenance requests through approvals, work orders, contractor assignment, and verification.
- Manage projects, contractors, tenders, grievances, and supporting documents.
- Provide dashboards, notifications, and an auditable record of important changes.
- Enforce role-based permissions and administrative-jurisdiction scoping in the API.

The project is an MVP. Government SSO, email/SMS delivery, and production-grade document storage are not implemented. See [docs/security.md](docs/security.md) and [docs/architecture.md](docs/architecture.md) for scope and security notes.

## Technology

| Area | Technologies |
|---|---|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query |
| Maps and charts | MapLibre GL, Turf.js, Recharts |
| Backend | Python 3.11+, FastAPI, Pydantic, SQLAlchemy, Alembic |
| Database | PostgreSQL 14+; PostGIS is not required |
| Documents | Local filesystem storage under `backend/uploads/` |

## Run locally

### Prerequisites

- Windows with PowerShell (commands below), or adapt the activation/copy commands for your shell
- Node.js 18+ and npm
- Python 3.11+
- PostgreSQL 14+

### 1. Create local databases

From the repository root, run the SQL setup script as a PostgreSQL superuser. If `psql` is not on your `PATH`, use its full path, for example:

```powershell
psql -U postgres -f scripts\setup_local_db.sql
```

This creates the `rb_admin` role, the `rb_assets` development database, and the separate `rb_assets_test` database used by the test suite. The local role password is `rb_dev_password`.

### 2. Configure the frontend and backend

The checked-in example contains local defaults. Copy it into each app directory so Vite and the backend each load their own environment file:

```powershell
Copy-Item .env.example frontend\.env.local
Copy-Item .env.example backend\.env
```

The example database URL matches the SQL setup script. If your PostgreSQL username, password, host, or database differs, update `DATABASE_URL` in `backend\.env`. Before exposing the app beyond local development, replace `SECRET_KEY` with a strong secret and restrict `BACKEND_CORS_ORIGINS` to the frontend's exact origin.

### 3. Install, migrate, and seed the backend

In a PowerShell terminal:

```powershell
Set-Location backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
python -m seed.seed_data
uvicorn app.main:app --reload
```

The API is available at [http://localhost:8000](http://localhost:8000), its health check at [http://localhost:8000/health](http://localhost:8000/health), and interactive API documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

### 4. Start the frontend

In a second terminal from the repository root:

```powershell
Set-Location frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The default API URL is `http://localhost:8000/api/v1`; change `VITE_API_BASE_URL` in `frontend\.env.local` if your backend runs elsewhere.

### 5. Sign in

All seeded accounts use the password `Password123!`:

| Email | Role |
|---|---|
| `state.admin@rnb.gov.in` | State administrator |
| `dept.admin@rnb.gov.in` | Department administrator |
| `field.engineer@rnb.gov.in` | Field engineer / inspector |
| `maintenance.officer@rnb.gov.in` | Maintenance officer |
| `contractor.user@rnb.gov.in` | Contractor |

Seed records are fictional demo data, not government records. **Running the seed command again refreshes generated business data** (including assets, inspections, projects, grievances, and tenders); do not run it against a database containing data you need to keep.

## Tests and quality checks

Backend tests (run from `backend/` with the virtual environment activated):

```powershell
pytest
```

The test suite uses `rb_assets_test`, not the demo database. The SQL setup script creates this database. If it is unavailable, database-backed tests are skipped; set `TEST_DATABASE_URL` to use a different test database.

Frontend checks (run from `frontend/`):

```powershell
npm run lint
npm run build
```

## Repository map

```text
backend/
  app/          FastAPI routes, schemas, models, services, auth, and permissions
  migrations/   Alembic database migrations
  seed/         Synthetic demo-data loader
  tests/        Backend test suite
  uploads/      Local document files (generated; not committed)
frontend/
  src/          React screens, components, API client, hooks, and routes
docs/           Setup, architecture, API, database, deployment, and security guides
scripts/        Local PostgreSQL setup script
```

## Documentation

- [Setup and troubleshooting](docs/setup.md)
- [Architecture](docs/architecture.md)
- [Database schema](docs/database.md)
- [API endpoints](docs/api.md)
- [Security notes](docs/security.md)
- [Vercel deployment](docs/deployment.md)

## Deployment and limitations

See [docs/deployment.md](docs/deployment.md) for the Vercel frontend/backend and Neon PostgreSQL setup. Vercel's function filesystem is temporary, so uploaded documents do not persist there; production deployment needs external object storage. The local filesystem storage is intended for development and demos.
