from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.enums import SystemRole
from app.models.geo import Department
from app.schemas.geo import DepartmentCreate, DepartmentRead

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentRead])
def list_departments(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Department).order_by(Department.name).all()


@router.post("", response_model=DepartmentRead, status_code=201)
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles(SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN)),
):
    if db.query(Department).filter(Department.code == payload.code).first():
        raise HTTPException(status_code=409, detail="Department code already exists")
    dept = Department(**payload.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept
