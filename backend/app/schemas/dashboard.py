from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_receivable: float
    total_payable: float
    active_count: int
    overdue_count: int
