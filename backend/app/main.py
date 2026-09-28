from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    admin_units,
    approvals,
    asset_types,
    assets,
    audit_logs,
    auth,
    condition,
    contractors,
    departments,
    documents,
    gis,
    grievances,
    inspections,
    maintenance,
    notifications,
    projects,
    reports,
    tenders,
    users,
    work_orders,
)

def init_db():
    try:
        from pathlib import Path
        from alembic import command
        from alembic.config import Config
        from app.database import engine, SessionLocal
        from app.models.user import User

        backend_dir = Path(__file__).resolve().parent.parent
        alembic_ini = backend_dir / "alembic.ini"
        if alembic_ini.exists():
            alembic_cfg = Config(str(alembic_ini))
            alembic_cfg.set_main_option("script_location", str(backend_dir / "migrations"))
            command.upgrade(alembic_cfg, "head")
        else:
            from app.database import Base
            from app import models  # noqa
            Base.metadata.create_all(bind=engine)

        with SessionLocal() as db:
            if db.query(User).count() == 0:
                print("No users found in database — running seed...")
                from seed.seed_data import run as run_seed
                run_seed()
                print("Initial seed completed.")
    except Exception as exc:
        print(f"init_db non-fatal exception: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

for router in (
    auth.router,
    users.router,
    departments.router,
    admin_units.router,
    asset_types.router,
    assets.router,
    gis.router,
    inspections.router,
    condition.router,
    maintenance.router,
    work_orders.router,
    projects.router,
    contractors.router,
    documents.router,
    approvals.router,
    notifications.router,
    reports.router,
    audit_logs.router,
    grievances.router,
    tenders.router,
):
    app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/health/db")
def health_db():
    from app.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            table_count = conn.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")
            ).scalar()
            user_count = None
            try:
                user_count = conn.execute(text("SELECT count(*) FROM users")).scalar()
            except Exception:
                pass
            return {
                "status": "ok",
                "database": "connected",
                "table_count": table_count,
                "user_count": user_count,
            }
    except Exception as e:
        import re
        masked_url = re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", settings.DATABASE_URL)
        return {"status": "error", "error": str(e), "db_url": masked_url}


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "docs": "/docs"}
