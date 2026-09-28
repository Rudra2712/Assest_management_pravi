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
from app.permissions.jurisdiction import user_role_codes

router = APIRouter(prefix="/contractors", tags=["contractors"])


@router.get("", response_model=list[ContractorRead])
def list_contractors(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    roles = user_role_codes(user)
    if SystemRole.CONTRACTOR.value in roles:
        return db.query(Contractor).filter(Contractor.user_id == user.id, Contractor.is_active.is_(True)).all()
    if not roles & {SystemRole.STATE_ADMIN.value, SystemRole.DEPARTMENT_ADMIN.value, SystemRole.MAINTENANCE_OFFICER.value}:
        raise HTTPException(status_code=403, detail="Insufficient role to view contractor profiles")
    return db.query(Contractor).filter(Contractor.is_active.is_(True)).order_by(Contractor.name).all()


@router.post("", response_model=ContractorRead, status_code=201)
def create_contractor(
    payload: ContractorCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN)),
):
    contractor = Contractor(**payload.model_dump())
    db.add(contractor)
    db.flush()
    record_audit(db, actor_id=user.id, action="CONTRACTOR_CREATE", entity_type="contractor", entity_id=contractor.id, new_value={"name": contractor.name})
    db.commit()
    db.refresh(contractor)
    return contractor


@router.get("/{contractor_id}", response_model=ContractorRead)
def get_contractor(contractor_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    contractor = db.get(Contractor, contractor_id)
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    roles = user_role_codes(user)
    if SystemRole.CONTRACTOR.value in roles and contractor.user_id != user.id:
        raise HTTPException(status_code=404, detail="Contractor not found")
    if SystemRole.CONTRACTOR.value not in roles and not roles & {SystemRole.STATE_ADMIN.value, SystemRole.DEPARTMENT_ADMIN.value, SystemRole.MAINTENANCE_OFFICER.value}:
        raise HTTPException(status_code=403, detail="Insufficient role to view contractor profiles")
    return contractor
