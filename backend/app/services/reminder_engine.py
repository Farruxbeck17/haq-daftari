import logging
from datetime import datetime, timedelta, timezone
from html import escape

from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.bot.bot_instance import bot
from app.core.config import settings
from app.core.database import SessionLocal
from app.models import DebtTransaction as Debt, TransactionType as Kind, User
from app.services.eskiz_sms import SmsError, sms
from app.services.ledger import OPEN_STATUSES, today

logger = logging.getLogger(__name__)


def reminder_text(debt, tone="friendly"):
    deadline = debt.due_date.strftime("%d.%m.%Y") if debt.due_date else "Belgilanmagan"
    amount = f"{debt.remaining_amount:,.2f}".replace(",", " ")
    if tone == "formal":
        return (f"Hurmatli foydalanuvchi, o'zaro hisob-kitob bo'yicha eslatma. "
                f"Qolgan summa: {amount} {debt.currency}. Muddat: {deadline}. "
                "Imkoningiz bo'lganda hisob-kitobni amalga oshirishingizni so'raymiz. Rahmat.")
    return (f"Assalomu alaykum! O'zaro hisob-kitobni muloyim eslatib qo'ymoqchimiz. "
            f"Qolgan summa: {amount} {debt.currency}. Muddat: {deadline}. "
            "Qulay paytda hisob-kitob qilsangiz, xursand bo'lamiz. Rahmat! 🤝")


async def deliver_reminder(db, debt, tone="friendly"):
    if debt.status not in OPEN_STATUSES:
        raise HTTPException(409, "Bu qarz uchun eslatma yuborib bo'lmaydi")
    now = datetime.now(timezone.utc)
    if debt.last_reminder_sent_at and now - debt.last_reminder_sent_at < timedelta(hours=24):
        raise HTTPException(429, "Eslatma har 24 soatda bir marta yuboriladi")
    debtor = debt.counterparty if debt.type == Kind.GIVEN else debt.creator
    phone = debt.counterparty_phone if debt.type == Kind.GIVEN else None
    if debtor is None and not phone:
        raise HTTPException(422, "Eslatma uchun tasdiqlash yoki telefon raqami kerak")
    payer = None
    if debtor is None:
        payer = (await db.execute(select(User).where(User.id == debt.creator_id).with_for_update())).scalar_one()
        if settings.ESKIZ_EMAIL and payer.sms_balance <= 0:
            raise HTTPException(402, "SMS hisobingizda mablag' yetarli emas")
        if settings.ENVIRONMENT == "production" and not settings.ESKIZ_EMAIL:
            raise HTTPException(503, "SMS xizmati sozlanmagan")
    # Yuborishdan avval vaqt saqlanadi: noaniq tarmoq javobi qayta xabar yubormaydi.
    debt.last_reminder_sent_at = now
    if payer is not None and settings.ESKIZ_EMAIL:
        payer.sms_balance -= 1
    await db.commit()
    message = reminder_text(debt, tone)
    try:
        if debtor is not None:
            await bot.send_message(debtor.telegram_id, escape(message))
            return {"message": "Eslatma Telegram xizmatiga topshirildi", "channel": "telegram"}
        await sms.send(phone, message)
        return {"message": "Sinov eslatmasi yozildi" if not settings.ESKIZ_EMAIL else "Eslatma SMS xizmatiga topshirildi",
                "channel": "mock_sms" if not settings.ESKIZ_EMAIL else "sms"}
    except (TelegramAPIError, SmsError):
        logger.warning("Eslatmani yuborish tasdiqlanmadi: %s", debt.id)
        raise HTTPException(502, "Yuborish tasdiqlanmadi. Takroriy xabar oldini olish uchun 24 soat kuting") from None


async def send_daily_reminders():
    cutoff = today() + timedelta(days=3)
    async with SessionLocal() as db:
        ids = list((await db.scalars(select(Debt.id).where(
            Debt.status.in_(OPEN_STATUSES), Debt.due_date <= cutoff,
            (Debt.due_date <= today()) | (Debt.due_date == cutoff)
        ).order_by(Debt.id))).all())
    for debt_id in ids:
        try:
            async with SessionLocal() as db:
                debt = (await db.execute(select(Debt).where(Debt.id == debt_id)
                    .with_for_update(skip_locked=True, of=Debt)
                    .options(selectinload(Debt.creator), selectinload(Debt.counterparty)))).scalar_one_or_none()
                if debt is not None:
                    await deliver_reminder(db, debt)
        except HTTPException as exc:
            if exc.status_code != 429:
                logger.warning("Eslatma o'tkazib yuborildi: %s, kod %s", debt_id, exc.status_code)
        except Exception:
            logger.exception("Kundalik eslatmada xatolik: %s", debt_id)


def create_scheduler():
    scheduler = AsyncIOScheduler(timezone="Asia/Tashkent")
    scheduler.add_job(send_daily_reminders, "cron", hour=9, minute=0,
                      id="daily_reminders", replace_existing=True, max_instances=1,
                      coalesce=True, misfire_grace_time=3600)
    return scheduler
