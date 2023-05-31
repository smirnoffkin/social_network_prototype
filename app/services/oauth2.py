from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.postgres.connection import get_db
from app.db.postgres.models import User
from app.services.security import Hasher
from app.services.user import _get_user_by_email

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.ACCESS_TOKEN_URL)


async def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})

    return jwt.encode(
        claims=to_encode,
        key=settings.SECRET_KEY,
        algorithm=settings.JWT_ENCODE_ALGORITHM,
    )


async def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token=token,
            key=settings.SECRET_KEY,
            algorithms=[settings.JWT_ENCODE_ALGORITHM],
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return payload


async def authenticate_user(
    email: str,
    password: str,
    db: AsyncSession = Depends(get_db)
) -> User | None:
    user = await _get_user_by_email(email, db)
    if user is None:
        return
    if not Hasher.verify_password(password, user.password):
        return
    return user


async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload: dict = await verify_access_token(token)
    email: str = payload.get("sub")
    current_user = await _get_user_by_email(email, db)

    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return current_user
