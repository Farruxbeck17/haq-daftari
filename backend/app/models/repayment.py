from uuid import uuid4

from sqlalchemy import BigInteger, CheckConstraint, Column, DateTime, ForeignKey, Numeric, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class RepaymentHistory(Base):
    __tablename__ = "repayment_history"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_repayment_amount"),
        UniqueConstraint("transaction_id", "idempotency_key", name="uq_repayment_request"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("debt_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Numeric(14, 2), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    note = Column(Text)
    recorded_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"))
    idempotency_key = Column(UUID(as_uuid=True), nullable=False)
    transaction = relationship("DebtTransaction", back_populates="repayments")
