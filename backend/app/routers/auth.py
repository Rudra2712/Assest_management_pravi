from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.auth.security import create_access_token, create_refresh_token, decode_token, verify_password
from app.database import get_db
from app.models.contractor import Contractor
from app.models.user import User
from app.permissions.jurisdiction import jurisdiction_unit_ids, user_role_codes
from app.schemas.auth import CurrentUserRead, LoginRequest, RefreshRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    roles = list(user_role_codes(user))
    jurisdiction_ids = jurisdiction_unit_ids(db, user) or []
    access_token = create_access_token(user.id, roles, jurisdiction_ids)
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
        if decoded.get("type") != "refresh":
            raise ValueError("Not a refresh token")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    user = db.get(User, UUID(decoded["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return _issue_tokens(db, user)


@router.get("/me", response_model=CurrentUserRead)
def read_me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = CurrentUserRead.model_validate(user)
    data.roles = list(user_role_codes(user))
    contractor = db.query(Contractor).filter(Contractor.user_id == user.id).first()
    data.contractor_id = contractor.id if contractor else None
    return data
