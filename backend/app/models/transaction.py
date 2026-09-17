import enum
from uuid import uuid4

from sqlalchemy import BigInteger, CheckConstraint, Column, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TransactionType(str, enum.Enum):
    GIVEN = "GIVEN"
    TAKEN = "TAKEN"


class TransactionStatus(str, enum.Enum):
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    ACTIVE = "ACTIVE"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    SETTLED = "SETTLED"
    REJECTED = "REJECTED"


class DebtTransaction(Base):
    __tablename__ = "debt_transactions"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_debt_amount"),
        CheckConstraint("remaining_amount >= 0 AND remaining_amount <= amount", name="ck_debt_remaining"),
        CheckConstraint("counterparty_id IS NULL OR counterparty_id <> creator_id", name="ck_debt_parties"),
        CheckConstraint("currency = 'UZS'", name="ck_debt_currency"),
        Index("ix_debt_creator_created", "creator_id", "created_at"),
        Index("ix_debt_counterparty", "counterparty_id"),
        Index("ix_debt_status_due", "status", "due_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    creator_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    counterparty_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"))
    counterparty_name = Column(String(255), nullable=False)
    counterparty_phone = Column(String(32))
    type = Column(Enum(TransactionType, name="transactiontype"), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    remaining_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="UZS", server_default="UZS")
    due_date = Column(Date)
    status = Column(Enum(TransactionStatus, name="transactionstatus"), nullable=False, default=TransactionStatus.ACTIVE)
    confirmation_token = Column(UUID(as_uuid=True), default=uuid4, unique=True, index=True, nullable=False)
    note = Column(Text)
    last_reminder_sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_transactions", lazy="raise")
    counterparty = relationship("User", foreign_keys=[counterparty_id], back_populates="shared_transactions", lazy="raise")
    repayments = relationship("RepaymentHistory", back_populates="transaction", cascade="all, delete-orphan",
                              passive_deletes=True, order_by="RepaymentHistory.paid_at", lazy="raise")
