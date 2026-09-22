import uuid
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from src.engine.database import get_session
from src.engine.models import User
from src.auth.utils import verify_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_user_from_token(token: str, session: AsyncSession) -> Optional[User]:
    """Decode/verify a JWT and load the User it names.

    Returns None on any failure (missing/invalid/expired token, malformed or
    unknown subject) instead of raising, so this can be reused outside of
    FastAPI's HTTP dependency-injection — e.g. from the WebSocket endpoint,
    which authenticates via a `token` query param (browsers can't send
    custom WS headers) and isn't wired through `Depends`. `get_current_user`
    below is the HTTP-route wrapper that turns a None into a 401.
    """
    payload = verify_token(token)
    if payload is None:
        return None
    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        return None

    query = select(User).where(User.id == user_id)
    result = await session.execute(query)
    return result.scalars().first()

async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = await get_user_from_token(token, session)
    if user is None:
        raise credentials_exception
    return user
