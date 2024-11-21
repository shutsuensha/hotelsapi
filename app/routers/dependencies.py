from fastapi import Depends, Query, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from pydantic import BaseModel, Field
from app.database import async_session_maker
import jwt
from app.config import settings
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone, date


class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    location: str | None = None
    title: str | None = None
    date_from: date | None = None
    date_to: date | None = None


filter = Annotated[FilterParams, Query()]


async def get_db():
    async with async_session_maker() as session:
        yield session


db = Annotated[AsyncSession, Depends(get_db)]


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode |= {"exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def encode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except (jwt.exceptions.DecodeError, jwt.exceptions.ExpiredSignatureError):
        raise HTTPException(status_code=401, detail="Неверный токен или токен истек")


def get_token(request: Request):
    token = request.cookies.get("access_token", None)
    if not token:
        raise HTTPException(status_code=401, detail="Вы не предоставили токен доступа")
    return token


def get_current_user_id(token: Annotated[str, Depends(get_token)]):
    data = encode_token(token)
    if datetime.now() > datetime.fromtimestamp(data["exp"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Token expired!")
    return data["user_id"]


user_id = Annotated[int, Depends(get_current_user_id)]
