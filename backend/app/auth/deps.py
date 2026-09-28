from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_token
from app.database import get_db
from app.models.user import User
from app.permissions.jurisdiction import user_role_codes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Not an access token")
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials") from exc

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def require_roles(*allowed_codes: str):
    allowed = {c.value if hasattr(c, "value") else c for c in allowed_codes}

    def _dep(user: User = Depends(get_current_user)) -> User:
        if not user_role_codes(user) & allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role for this action")
        return user

    return _dep
