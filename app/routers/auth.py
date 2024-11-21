from fastapi import APIRouter, HTTPException, Response, status
from app.routers.dependencies import (
    db,
    create_access_token,
    hash_password,
    verify_password,
    user_id,
)
from app.schemas.users import UserIn, UserOut
from app.models import UsersOrm
from sqlalchemy import insert, select

router = APIRouter(prefix="/auth", tags=["users"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserIn, db: db):
    user = await db.scalar(select(UsersOrm).where(UsersOrm.email == user_in.email))
    if user:
        raise HTTPException(status_code=409, detail="user already exists")
    user = await db.scalar(
        insert(UsersOrm)
        .values(email=user_in.email, hashed_password=hash_password(user_in.password))
        .returning(UsersOrm)
    )
    await db.commit()
    return user


@router.post("/login")
async def login_user(user_in: UserIn, response: Response, db: db):
    user = await db.scalar(select(UsersOrm).where(UsersOrm.email == user_in.email))
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь с таким email не зарегистрирован")
    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Пароль неверный")
    access_token = create_access_token({"user_id": user.id})
    response.set_cookie("access_token", access_token)
    return {"access_token": access_token}


@router.get("/me", response_model=UserOut)
async def get_me(user_id: user_id, db: db):
    user = await db.scalar(select(UsersOrm).where(UsersOrm.id == user_id))
    return user


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "OK"}
