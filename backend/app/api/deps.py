from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User

bearer = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                           db: AsyncSession = Depends(get_db)) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "Avval Telegram orqali kiring")
    payload = decode_access_token(credentials.credentials)
    user = await db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(401, "Foydalanuvchi topilmadi")
    return user
