from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token, UserOut
from app.core.security import verify_password, get_password_hash, create_access_token, create_refresh_token

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=201)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    access_token = create_access_token({"sub": user.username})
    refresh_token = create_refresh_token({"sub": user.username})
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/create-admin")
async def create_admin(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """One-time admin creation endpoint — disable after first use in production."""
    result = await db.execute(select(User).where(User.is_admin == True))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=403, detail="Admin already exists")

    user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        is_admin=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": "Admin created", "username": user.username}
