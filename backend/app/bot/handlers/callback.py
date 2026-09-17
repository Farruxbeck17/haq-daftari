import logging
from html import escape
from uuid import UUID

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from app.bot.bot_instance import bot
from app.core.database import SessionLocal
from app.models import DebtTransaction as Debt, TransactionStatus as Status, User
from app.services.users import upsert_user

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("confirm:") | F.data.startswith("reject:"))
async def confirm_or_reject(callback: CallbackQuery):
    if not isinstance(callback.message, Message) or callback.message.chat.type != "private":
        await callback.answer("Shaxsiy suhbat orqali tasdiqlang.", show_alert=True)
        return
    if callback.message.chat.id != callback.from_user.id:
        await callback.answer("Bu amal sizga tegishli emas.", show_alert=True)
        return
    try:
        action, raw_token = callback.data.split(":", 1)
        token = UUID(raw_token)
    except (ValueError, AttributeError):
        await callback.answer("Havola noto'g'ri.", show_alert=True)
        return
    async with SessionLocal() as db:
        user = await upsert_user(db, callback.from_user.model_dump())
        await db.commit()
        debt = (await db.execute(select(Debt).where(Debt.confirmation_token == token)
                                 .with_for_update())).scalar_one_or_none()
        if debt is None or debt.status != Status.PENDING_CONFIRMATION:
            await callback.answer("Bu yozuv allaqachon ko'rib chiqilgan.", show_alert=True)
            return
        if debt.creator_id == user.id:
            await callback.answer("O'z yozuvingizni tasdiqlay olmaysiz.", show_alert=True)
            return
        creator = await db.get(User, debt.creator_id)
        if action == "confirm":
            debt.counterparty_id = user.id
            debt.status = Status.ACTIVE
            text = "Qarz hisobi muvaffaqiyatli tasdiqlandi va daftaringizga kiritildi! 🤝"
            notification = f"{escape(user.first_name)} qarz yozuvini tasdiqladi. 🤝"
        else:
            debt.status = Status.REJECTED
            text = "Qarz yozuvi rad etildi."
            notification = f"{escape(user.first_name)} qarz yozuvini rad etdi."
        await db.commit()
    await callback.answer("Saqlandi")
    try:
        await callback.message.edit_text(text)
    except TelegramAPIError:
        logger.warning("Tasdiqlash xabarini tahrirlab bo'lmadi")
    try:
        await bot.send_message(creator.telegram_id, notification)
    except TelegramAPIError:
        logger.warning("Yozuv muallifiga bildirishnoma yuborilmadi: %s", debt.id)
