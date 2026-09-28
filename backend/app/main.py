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

app = FastAPI(title=settings.APP_NAME, openapi_url=f"{settings.API_V1_PREFIX}/openapi.json", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
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


@app.get("/")
def root():
    return {"name": settings.APP_NAME, "docs": "/docs"}
