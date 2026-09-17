import asyncio
import logging
import time

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class SmsError(Exception):
    """SMS xizmatida xatolik."""


class EskizSMS:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url="https://notify.eskiz.uz", timeout=15)
        self.token = None
        self.expires_at = 0
        self.lock = asyncio.Lock()

    async def authenticate(self):
        async with self.lock:
            if self.token and self.expires_at > time.monotonic():
                return
            response = await self.client.post("/api/auth/login", data={
                "email": settings.ESKIZ_EMAIL, "password": settings.ESKIZ_PASSWORD})
            response.raise_for_status()
            self.token = response.json()["data"]["token"]
            self.expires_at = time.monotonic() + 23 * 3600

    async def send(self, phone: str, message: str) -> bool:
        if not settings.ESKIZ_EMAIL:
            if settings.ENVIRONMENT == "production":
                raise SmsError("SMS xizmati sozlanmagan")
            logger.info("Sinov SMS: qabul qiluvchi oxiri %s, matn: %s", phone[-4:], message)
            return True
        try:
            await self.authenticate()
            response = await self.client.post("/api/message/sms/send",
                headers={"Authorization": f"Bearer {self.token}"},
                data={"mobile_phone": phone.removeprefix("+"), "message": message, "from": settings.ESKIZ_SENDER})
            if response.status_code == 401:
                self.token = None
                await self.authenticate()
                response = await self.client.post("/api/message/sms/send",
                    headers={"Authorization": f"Bearer {self.token}"},
                    data={"mobile_phone": phone.removeprefix("+"), "message": message, "from": settings.ESKIZ_SENDER})
            response.raise_for_status()
            if response.json().get("status") not in ("waiting", "success"):
                raise SmsError("SMS qabul qilinmadi")
            return True
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise SmsError("SMS xizmatiga ulanib bo'lmadi") from exc

    async def close(self):
        await self.client.aclose()


sms = EskizSMS()
