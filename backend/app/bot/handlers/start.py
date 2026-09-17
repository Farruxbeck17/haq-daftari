from html import escape
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import DebtTransaction as Debt, TransactionStatus as Status
from app.services.users import upsert_user

router = Router()


@router.message(CommandStart(), F.chat.type == "private")
async def start(message: Message, command: CommandObject):
    if message.from_user is None:
        return
    async with SessionLocal() as db:
        user = await upsert_user(db, message.from_user.model_dump())
        await db.commit()
        if command.args and command.args.startswith("confirm_"):
            try:
                token = UUID(command.args.removeprefix("confirm_"))
            except ValueError:
                await message.answer("Tasdiqlash havolasi noto'g'ri.")
                return
            debt = (await db.execute(select(Debt).where(Debt.confirmation_token == token)
                .options(selectinload(Debt.creator)))).scalar_one_or_none()
            if debt is None or debt.status != Status.PENDING_CONFIRMATION:
                await message.answer("Havola topilmadi yoki undan foydalanilgan.")
                return
            if debt.creator_id == user.id:
                await message.answer("Bu havolani hisob-kitobdagi do'stingizga yuboring.")
                return
            deadline = str(debt.due_date) if debt.due_date else "Belgilanmagan"
            direction = "Siz qarzdor sifatida qayd etilgansiz." if debt.type.value == "GIVEN" else "Siz haqdor sifatida qayd etilgansiz."
            text = (f"Assalomu alaykum! {escape(debt.creator.first_name)} siz bilan o'zaro hisob-kitobni qayd etdi:\n"
                    f"Summa: {debt.amount:,.2f} {debt.currency}\nMuddat: {deadline}\n"
                    f"Izoh: {escape(debt.note or 'Mavjud emas')}\n{direction}\n"
                    "Ushbu qarz yozuvini tasdiqlaysizmi?")
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"confirm:{token}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{token}")]])
            await message.answer(text, reply_markup=keyboard)
            return
    await message.answer("Assalomu alaykum! Haq daftari bilan o'zaro hisob-kitoblarni tartibli yuriting.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="📒 Daftarni ochish", web_app=WebAppInfo(url=settings.WEBAPP_URL))]]))
