from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.transaction import TransactionStatus, TransactionType

Money = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=2, allow_inf_nan=False)]


class TransactionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    counterparty_name: str = Field(min_length=1, max_length=255)
    counterparty_phone: str | None = Field(default=None, pattern=r"^\+998\d{9}$")
    type: TransactionType
    amount: Money
    currency: Literal["UZS"] = "UZS"
    due_date: date | None = None
    note: str | None = Field(default=None, max_length=1000)
    share_with_telegram: bool = False

    @field_validator("counterparty_phone", "note", mode="before")
    @classmethod
    def blank_to_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value


class RepaymentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    amount: Money
    note: str | None = Field(default=None, max_length=1000)
    idempotency_key: UUID


class RepaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    amount: Decimal
    paid_at: datetime
    note: str | None


class TransactionOut(BaseModel):
    id: UUID
    creator_id: int
    counterparty_id: int | None
    counterparty_name: str
    counterparty_phone: str | None
    type: TransactionType
    amount: Decimal
    remaining_amount: Decimal
    currency: str
    due_date: date | None
    status: TransactionStatus
    note: str | None
    last_reminder_sent_at: datetime | None
    created_at: datetime
    updated_at: datetime
    confirmation_link: str | None = None
    can_repay: bool
    can_remind: bool
    repayments: list[RepaymentOut] = Field(default_factory=list)


class ReminderRequest(BaseModel):
    tone: Literal["friendly", "formal"] = "friendly"
