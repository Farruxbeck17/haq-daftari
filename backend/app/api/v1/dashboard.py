from fastapi import APIRouter, Depends
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import DebtTransaction as Debt, TransactionType as Kind, User
from app.schemas.dashboard import DashboardSummary
from app.services.ledger import OPEN_STATUSES, involved, today

router = APIRouter(tags=["Umumiy hisob"])


@router.get("/dashboard", response_model=DashboardSummary)
async def dashboard(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    receivable = or_(and_(Debt.creator_id == user.id, Debt.type == Kind.GIVEN),
                     and_(Debt.counterparty_id == user.id, Debt.type == Kind.TAKEN))
    query = select(
        func.coalesce(func.sum(case((receivable, Debt.remaining_amount), else_=0)), 0),
        func.coalesce(func.sum(case((receivable, 0), else_=Debt.remaining_amount)), 0),
        func.count(Debt.id),
        func.count(case((Debt.due_date < today(), 1))),
    ).where(involved(user.id), Debt.status.in_(OPEN_STATUSES))
    received, payable, active, overdue = (await db.execute(query)).one()
    return DashboardSummary(total_receivable=float(received), total_payable=float(payable),
                            active_count=active, overdue_count=overdue)
