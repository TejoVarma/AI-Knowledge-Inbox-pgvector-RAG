import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import settings

# OWASP's low-memory argon2id profile (19 MiB) - safe on a 512 MB free-tier box
_hasher = PasswordHasher(memory_cost=19456, time_cost=2, parallelism=1)

# used when the email doesn't exist, so a wrong email takes as long as a wrong password
_DUMMY_HASH = _hasher.hash("not-a-real-password")

_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def burn_password_check(password: str) -> None:
    verify_password(password, _DUMMY_HASH)


def create_access_token(user_id: uuid.UUID, expires_in: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_in or timedelta(minutes=settings.jwt_expire_minutes))
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> uuid.UUID | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[_ALGORITHM])
        return uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
