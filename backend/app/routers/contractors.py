from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.database import get_db
from app.models.contractor import Contractor
from app.models.enums import SystemRole
from app.models.user import User
from app.schemas.contractor import ContractorCreate, ContractorRead
from app.utils.audit import record_audit

router = APIRouter(prefix="/contractors", tags=["contractors"])


@router.get("", response_model=list[ContractorRead])
def list_contractors(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Contractor).filter(Contractor.is_active.is_(True)).order_by(Contractor.name).all()


@router.post("", response_model=ContractorRead, status_code=201)
def create_contractor(
    payload: ContractorCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.CIRCLE_DIVISION_OFFICER)),
):
    contractor = Contractor(**payload.model_dump())
    db.add(contractor)
    db.flush()
    record_audit(db, actor_id=user.id, action="CONTRACTOR_CREATE", entity_type="contractor", entity_id=contractor.id, new_value={"name": contractor.name})
    db.commit()
    db.refresh(contractor)
    return contractor


@router.get("/{contractor_id}", response_model=ContractorRead)
def get_contractor(contractor_id: UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    contractor = db.get(Contractor, contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return contractor
