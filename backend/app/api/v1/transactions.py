from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import DebtTransaction as Debt, RepaymentHistory, TransactionStatus as Status, User
from app.schemas.transaction import ReminderRequest, RepaymentCreate, TransactionCreate, TransactionOut
from app.services.ledger import OPEN_STATUSES, get_debt, involved, is_creditor, may_record, present, today
from app.services.reminder_engine import deliver_reminder

router = APIRouter(prefix="/transactions", tags=["Qarzlar"])


@router.get("", response_model=list[TransactionOut])
async def list_transactions(tab: Literal["all", "overdue", "upcoming", "settled"] = "all",
                            limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                            user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    query = select(Debt).where(involved(user.id))
    if tab == "overdue":
        query = query.where(Debt.status.in_(OPEN_STATUSES), Debt.due_date < today())
    elif tab == "upcoming":
        query = query.where(Debt.status.in_(OPEN_STATUSES), Debt.due_date >= today())
    elif tab == "settled":
        query = query.where(Debt.status == Status.SETTLED)
    query = query.order_by(Debt.created_at.desc(), Debt.id.desc()).limit(limit).offset(offset).options(
        selectinload(Debt.creator), selectinload(Debt.counterparty), selectinload(Debt.repayments))
    return [present(debt, user.id) for debt in (await db.scalars(query)).all()]


@router.post("", response_model=TransactionOut, status_code=201)
async def create_transaction(body: TransactionCreate, user: User = Depends(get_current_user),
                             db: AsyncSession = Depends(get_db)):
    values = body.model_dump(exclude={"share_with_telegram"})
    debt = Debt(**values, creator_id=user.id, remaining_amount=body.amount,
                status=Status.PENDING_CONFIRMATION if body.share_with_telegram else Status.ACTIVE)
    db.add(debt)
    await db.flush()
    debt_id = debt.id
    await db.commit()
    return present(await get_debt(db, debt_id, user.id), user.id)


@router.get("/{debt_id}", response_model=TransactionOut)
async def detail(debt_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    return present(await get_debt(db, debt_id, user.id), user.id)


@router.post("/{debt_id}/repay", response_model=TransactionOut)
async def repay(debt_id: UUID, body: RepaymentCreate, user: User = Depends(get_current_user),
                db: AsyncSession = Depends(get_db)):
    debt = await get_debt(db, debt_id, user.id, lock=True)
    if not may_record(debt, user.id):
        raise HTTPException(403, "To'lovni faqat haqdor qayd etishi mumkin")
    previous = next((item for item in debt.repayments if item.idempotency_key == body.idempotency_key), None)
    if previous:
        if previous.amount != body.amount or previous.note != body.note:
            raise HTTPException(409, "Bu so'rov kaliti boshqa to'lov uchun ishlatilgan")
        return present(debt, user.id)
    if debt.status not in OPEN_STATUSES:
        raise HTTPException(409, "Bu qarz bo'yicha to'lov qayd etib bo'lmaydi")
    if body.amount > debt.remaining_amount:
        raise HTTPException(422, "To'lov qolgan qarzdan oshmasligi kerak")
    debt.remaining_amount -= body.amount
    debt.status = Status.SETTLED if debt.remaining_amount == 0 else Status.PARTIALLY_PAID
    item = RepaymentHistory(transaction_id=debt.id, amount=body.amount, note=body.note,
                            idempotency_key=body.idempotency_key, recorded_by_id=user.id)
    debt.repayments.append(item)
    await db.flush()
    await db.refresh(debt, attribute_names=["updated_at"])
    await db.commit()
    return present(debt, user.id)


@router.post("/{debt_id}/send-reminder")
async def send_reminder(debt_id: UUID, body: ReminderRequest, user: User = Depends(get_current_user),
                        db: AsyncSession = Depends(get_db)):
    debt = await get_debt(db, debt_id, user.id, lock=True)
    if not is_creditor(debt, user.id):
        raise HTTPException(403, "Eslatmani faqat haqdor yuborishi mumkin")
    return await deliver_reminder(db, debt, body.tone)
