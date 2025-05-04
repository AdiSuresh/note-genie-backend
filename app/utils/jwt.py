from jose import JWTError, jwt
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from app.core.settings import settings


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, settings.jwt_secret, JWT_ALGORITHM=settings.jwt_algorithm)

def decode_token(token: str):
    try:
        return jwt.decode(token, settings.jwt_secret, JWT_ALGORITHMs=[settings.jwt_algorithm])
    except JWTError:
        return None
