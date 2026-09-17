from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import DebtTransaction as Debt, TransactionStatus as Status, TransactionType as Kind
from app.schemas.transaction import RepaymentOut, TransactionOut

OPEN_STATUSES = (Status.ACTIVE, Status.PARTIALLY_PAID)


def today():
    return datetime.now(ZoneInfo("Asia/Tashkent")).date()


def involved(user_id):
    return or_(Debt.creator_id == user_id, and_(Debt.counterparty_id == user_id,
               Debt.status.in_((Status.ACTIVE, Status.PARTIALLY_PAID, Status.SETTLED))))


def is_creditor(debt, user_id):
    return (debt.creator_id == user_id and debt.type == Kind.GIVEN) or (
        debt.counterparty_id == user_id and debt.type == Kind.TAKEN)


def may_record(debt, user_id):
    return is_creditor(debt, user_id) or (debt.creator_id == user_id and debt.counterparty_id is None)


async def get_debt(db, debt_id, user_id, lock=False):
    query = select(Debt).where(Debt.id == debt_id, involved(user_id)).options(
        selectinload(Debt.creator), selectinload(Debt.counterparty), selectinload(Debt.repayments))
    if lock:
        query = query.with_for_update(of=Debt)
    debt = (await db.execute(query)).scalar_one_or_none()
    if debt is None:
        raise HTTPException(404, "Qarz yozuvi topilmadi")
    return debt


def present(debt, user_id):
    own = debt.creator_id == user_id
    open_debt = debt.status in OPEN_STATUSES
    return TransactionOut(
        id=debt.id, creator_id=debt.creator_id, counterparty_id=debt.counterparty_id,
        counterparty_name=debt.counterparty_name if own else debt.creator.first_name,
        counterparty_phone=debt.counterparty_phone if own else None,
        type=debt.type if own else (Kind.TAKEN if debt.type == Kind.GIVEN else Kind.GIVEN),
        amount=debt.amount, remaining_amount=debt.remaining_amount, currency=debt.currency,
        due_date=debt.due_date, status=debt.status, note=debt.note,
        last_reminder_sent_at=debt.last_reminder_sent_at, created_at=debt.created_at, updated_at=debt.updated_at,
        confirmation_link=(f"https://t.me/{settings.BOT_USERNAME}?start=confirm_{debt.confirmation_token}"
                           if own and debt.status == Status.PENDING_CONFIRMATION else None),
        can_repay=open_debt and may_record(debt, user_id),
        can_remind=open_debt and is_creditor(debt, user_id),
        repayments=[RepaymentOut.model_validate(item) for item in debt.repayments],
    )
