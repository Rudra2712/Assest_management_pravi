from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import SystemRole
from app.models.geo import AdministrativeUnit
from app.schemas.geo import AdministrativeUnitCreate, AdministrativeUnitRead

router = APIRouter(prefix="/admin-units", tags=["administrative-units"])


def _compute_path(db: Session, parent_id, own_id) -> str:
    if parent_id is None:
        return str(own_id)
    parent = db.get(AdministrativeUnit, parent_id)
    if parent is None:
        raise HTTPException(status_code=400, detail="Parent administrative unit not found")
    return f"{parent.path}.{own_id}"


@router.get("", response_model=list[AdministrativeUnitRead])
def list_admin_units(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(AdministrativeUnit).order_by(AdministrativeUnit.path).all()


@router.post("", response_model=AdministrativeUnitRead, status_code=201)
def create_admin_unit(
    payload: AdministrativeUnitCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN)),
):
    if db.query(AdministrativeUnit).filter(AdministrativeUnit.code == payload.code).first():
        raise HTTPException(status_code=409, detail="Administrative unit code already exists")

    unit = AdministrativeUnit(code=payload.code, name=payload.name, level=payload.level, parent_id=payload.parent_id, path="")
    db.add(unit)
    db.flush()  # assigns unit.id without committing
    unit.path = _compute_path(db, payload.parent_id, unit.id)
    db.commit()
    db.refresh(unit)
    return unit
