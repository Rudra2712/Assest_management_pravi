from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.auth.security import hash_password
from app.database import get_db
from app.models.enums import SystemRole
from app.models.user import Role, User, UserRole
from app.permissions.jurisdiction import user_role_codes
from app.schemas.user import RoleAssign, UserCreate, UserRead, UserUpdate
from app.utils.audit import record_audit

router = APIRouter(prefix="/users", tags=["users"])


def _to_read(user: User) -> UserRead:
    data = UserRead.model_validate(user)
    data.roles = list(user_role_codes(user))
    return data


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _=Depends(require_roles(SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN, SystemRole.CIRCLE_DIVISION_OFFICER)),
):
    users = db.query(User).order_by(User.full_name).all()
    return [_to_read(u) for u in users]


@router.post("", response_model=UserRead, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN)),
):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        phone=payload.phone,
        department_id=payload.department_id,
        administrative_unit_id=payload.administrative_unit_id,
    )
    db.add(user)
    db.flush()

    for code in payload.role_codes:
        role = db.query(Role).filter(Role.code == code).first()
        if not role:
            raise HTTPException(status_code=400, detail=f"Unknown role code '{code}'")
        db.add(UserRole(user_id=user.id, role_id=role.id))

    record_audit(db, actor_id=current_user.id, action="USER_CREATE", entity_type="user", entity_id=user.id, new_value={"email": user.email})
    db.commit()
    db.refresh(user)
    return _to_read(user)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_value = {"is_active": user.is_active, "full_name": user.full_name}
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)

    record_audit(db, actor_id=current_user.id, action="USER_UPDATE", entity_type="user", entity_id=user.id, old_value=old_value, new_value=payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(user)
    return _to_read(user)


@router.post("/{user_id}/roles", response_model=UserRead)
def assign_role(
    user_id: UUID,
    payload: RoleAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(SystemRole.STATE_ADMIN, SystemRole.DEPARTMENT_ADMIN)),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role = db.query(Role).filter(Role.code == payload.role_code).first()
    if not role:
        raise HTTPException(status_code=400, detail="Unknown role code")

    db.add(UserRole(user_id=user.id, role_id=role.id, jurisdiction_unit_id=payload.jurisdiction_unit_id))
    record_audit(db, actor_id=current_user.id, action="USER_ROLE_GRANT", entity_type="user", entity_id=user.id, new_value={"role_code": payload.role_code})
    db.commit()
    db.refresh(user)
    return _to_read(user)
