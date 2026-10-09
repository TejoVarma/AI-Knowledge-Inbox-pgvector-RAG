from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import (
    ACCESS_COOKIE,
    CSRF_COOKIE,
    burn_password_check,
    create_access_token,
    create_csrf_token,
    hash_password,
    verify_password,
)
from app.db.database import get_db
from app.db.models import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth")
logger = get_logger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="an account with this email already exists"
        ) from exc

    db.refresh(user)
    logger.info("user registered", extra={"extra_fields": {"user_id": str(user.id)}})
    return user


@router.post("/login", response_model=UserResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> User:
    # the browser login: the token goes into an httpOnly cookie and never reaches javascript
    user = _authenticate(db, payload.email, payload.password)
    max_age = settings.jwt_expire_minutes * 60
    cookie_flags = {"max_age": max_age, "secure": settings.cookie_secure, "samesite": "lax", "path": "/"}

    response.set_cookie(ACCESS_COOKIE, create_access_token(user.id), httponly=True, **cookie_flags)
    # readable on purpose - the frontend copies it into the X-CSRF-Token header
    response.set_cookie(CSRF_COOKIE, create_csrf_token(), httponly=False, **cookie_flags)

    logger.info("user logged in", extra={"extra_fields": {"user_id": str(user.id), "via": "cookie"}})
    return user


@router.post("/token", response_model=TokenResponse)
def token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenResponse:
    # for /docs, tests and scripts: a bearer token in the body instead of cookies
    if len(form.password) > 128:
        # same cap as LoginRequest, so neither path hashes megabyte-sized "passwords"
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="password too long")
    user = _authenticate(db, form.username.strip().lower(), form.password)
    logger.info("user logged in", extra={"extra_fields": {"user_id": str(user.id), "via": "token"}})
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    # the jwt stays valid until it expires; removing it from the browser is what logout can do
    response.delete_cookie(ACCESS_COOKIE, path="/", secure=settings.cookie_secure, samesite="lax")
    response.delete_cookie(CSRF_COOKIE, path="/", secure=settings.cookie_secure, samesite="lax")


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def _authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))

    if user is None:
        burn_password_check(password)
        valid = False
    else:
        valid = verify_password(password, user.password_hash)

    # same message for unknown email and wrong password, so the form can't be used
    # to find out who has an account
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
