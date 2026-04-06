from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from src.engine.database import get_session
from src.engine.models import User
from src.auth.utils import hash_password, verify_password, create_access_token

auth_router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

@auth_router.post("/register", response_model=dict)
async def register(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    query = select(User).where(User.username == user_data.username)
    result = await session.execute(query)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_pwd = hash_password(user_data.password)
    new_user = User(username=user_data.username, hashed_password=hashed_pwd)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return {"message": "User created successfully", "user_id": str(new_user.id)}

@auth_router.post("/token", response_model=Token)
async def login(user_data: UserCreate, session: AsyncSession = Depends(get_session)):
    query = select(User).where(User.username == user_data.username)
    result = await session.execute(query)
    user = result.scalars().first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}
