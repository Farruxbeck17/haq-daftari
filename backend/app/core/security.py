import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qsl

from fastapi import HTTPException
from jose import JWTError, jwt

from app.core.config import settings


def verify_telegram_init_data(init_data: str, bot_token: str) -> dict:
    try:
        if not init_data or len(init_data) > 16384:
            raise ValueError("Hajm noto'g'ri")
        pairs = parse_qsl(init_data, keep_blank_values=True, strict_parsing=True)
        data = dict(pairs)
        if len(pairs) != len(data):
            raise ValueError("Takrorlangan kalit")
        supplied_hash = data.pop("hash")
        check_string = "\n".join(f"{key}={data[key]}" for key in sorted(data))
        secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, supplied_hash):
            raise ValueError("Imzo noto'g'ri")
        age = time.time() - int(data["auth_date"])
        if age < -30 or age > settings.INIT_DATA_MAX_AGE_SECONDS:
            raise ValueError("Kirish muddati tugagan")
        user = json.loads(data["user"])
        if not isinstance(user, dict) or type(user.get("id")) is not int:
            raise ValueError("Foydalanuvchi noto'g'ri")
        if not 0 < user["id"] < 2**63 or user.get("is_bot", False):
            raise ValueError("Foydalanuvchi noto'g'ri")
        if not isinstance(user.get("first_name"), str) or not 1 <= len(user["first_name"]) <= 255:
            raise ValueError("Ism noto'g'ri")
        for key in ("last_name", "username"):
            if user.get(key) is not None and (not isinstance(user[key], str) or len(user[key]) > 255):
                raise ValueError("Foydalanuvchi ma'lumoti noto'g'ri")
        return user
    except (KeyError, ValueError, TypeError, OverflowError):
        raise HTTPException(401, "Telegram orqali qayta kiring") from None


def create_access_token(data: dict) -> str:
    payload = data.copy()
    now = datetime.now(timezone.utc)
    payload.update(iat=now, exp=now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                   iss="qarzdaftar", aud="qarzdaftar-miniapp")
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM],
                             issuer="qarzdaftar", audience="qarzdaftar-miniapp",
                             options={"require_exp": True, "require_iat": True, "require_sub": True})
        if not isinstance(payload.get("sub"), str) or not payload["sub"].isdigit():
            raise ValueError("Foydalanuvchi noto'g'ri")
        if not 0 < int(payload["sub"]) < 2**63:
            raise ValueError("Foydalanuvchi noto'g'ri")
        return payload
    except (JWTError, ValueError, TypeError):
        raise HTTPException(401, "Kirish muddati tugagan. Telegram orqali qayta kiring") from None
