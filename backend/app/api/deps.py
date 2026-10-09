import secrets

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import ACCESS_COOKIE, CSRF_COOKIE, CSRF_HEADER, decode_access_token
from app.db.database import get_db
from app.db.models import User

# reads "Authorization: Bearer ..." and powers the Authorize button in /docs
_bearer = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def get_current_user(
    request: Request,
    bearer_token: str | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if bearer_token:
        # another site can't make the browser add this header, so no csrf check needed
        token = bearer_token
    else:
        token = request.cookies.get(ACCESS_COOKIE)
        if not token:
            raise unauthorized
        # the browser attaches cookies to requests other sites trigger, so anything
        # that changes data must also prove it came from our own frontend
        if request.method not in _SAFE_METHODS:
            _check_csrf(request)

    user_id = decode_access_token(token)
    if user_id is None:
        raise unauthorized

    # the token can outlive the account, so check the user still exists
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


def _check_csrf(request: Request) -> None:
    cookie_value = request.cookies.get(CSRF_COOKIE)
    header_value = request.headers.get(CSRF_HEADER)
    if not cookie_value or not header_value or not secrets.compare_digest(cookie_value, header_value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="csrf check failed")
