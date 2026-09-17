from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, verify_telegram_init_data
from app.schemas.auth import TelegramAuthRequest, TokenResponse, UserOut
from app.services.users import upsert_user

router = APIRouter(prefix="/auth", tags=["Kirish"])


@router.post("/telegram", response_model=TokenResponse)
async def telegram_auth(body: TelegramAuthRequest, db: AsyncSession = Depends(get_db)):
    data = verify_telegram_init_data(body.init_data, settings.BOT_TOKEN)
    user = await upsert_user(db, data)
    await db.commit()
    return TokenResponse(access_token=create_access_token({"sub": str(user.id)}), user=UserOut.model_validate(user))
