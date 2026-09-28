from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.deps import require_roles
from app.database import get_db
from app.models.enums import SystemRole
from app.models.user import User
from app.services.csv_import_service import commit_import, parse_csv, validate_and_preview

router = APIRouter(prefix="/imports", tags=["imports"])

_IMPORT_ROLES = [r.value for r in [SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.CIRCLE_DIVISION_OFFICER]]


@router.post("/assets/preview")
async def preview_asset_import(
    file: UploadFile,
    db: Session = Depends(get_db),
    _=Depends(require_roles(*_IMPORT_ROLES)),
):
    content = await file.read()
    try:
        rows = parse_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return validate_and_preview(db, rows)


@router.post("/assets/commit")
async def commit_asset_import(
    file: UploadFile,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*_IMPORT_ROLES)),
):
    content = await file.read()
    try:
        rows = parse_csv(content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    result = commit_import(db, rows, user)
    db.commit()
    return result
