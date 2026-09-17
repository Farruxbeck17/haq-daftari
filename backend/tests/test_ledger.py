from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.core.database import Base
from app.models import TransactionStatus as Status, TransactionType as Kind
from app.services.ledger import is_creditor, may_record, present
from app.services import reminder_engine as reminders


def debt(kind=Kind.GIVEN, status=Status.ACTIVE):
    return SimpleNamespace(
        id=uuid4(), creator_id=1, counterparty_id=2, counterparty_name="Vali",
        counterparty_phone="+998901234567", type=kind, amount=Decimal("100.00"),
        remaining_amount=Decimal("70.00"), currency="UZS", due_date=date(2026, 9, 10),
        status=status, note="<b>Izoh</b>", last_reminder_sent_at=None,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        confirmation_token=uuid4(), creator=SimpleNamespace(first_name="Ali", telegram_id=111),
        counterparty=SimpleNamespace(first_name="Vali", telegram_id=222), repayments=[])


def test_dual_sided_presentation():
    item = debt()
    assert present(item, 1).type == Kind.GIVEN
    other = present(item, 2)
    assert other.type == Kind.TAKEN
    assert other.counterparty_name == "Ali"
    assert other.counterparty_phone is None
    assert not other.can_repay
    assert not other.can_remind


def test_creditor_records_shared_taken_debt():
    item = debt(Kind.TAKEN)
    assert not may_record(item, 1)
    assert is_creditor(item, 2)
    assert may_record(item, 2)
    item.counterparty_id = None
    assert may_record(item, 1)


def test_pending_link_is_only_for_creator():
    item = debt(status=Status.PENDING_CONFIRMATION)
    assert present(item, 1).confirmation_link
    assert present(item, 2).confirmation_link is None
    assert not present(item, 1).can_repay


@pytest.mark.parametrize("kind,expected", [(Kind.GIVEN, 222), (Kind.TAKEN, 111)])
async def test_reminder_targets_real_debtor(monkeypatch, kind, expected):
    item = debt(kind)
    sender = AsyncMock()
    monkeypatch.setattr(reminders.bot, "send_message", sender)
    db = SimpleNamespace(commit=AsyncMock())
    result = await reminders.deliver_reminder(db, item)
    assert result["channel"] == "telegram"
    assert sender.call_args.args[0] == expected
    assert item.last_reminder_sent_at is not None
    db.commit.assert_awaited_once()


async def test_cooldown_blocks_network(monkeypatch):
    item = debt()
    item.last_reminder_sent_at = datetime.now(timezone.utc) - timedelta(hours=23)
    sender = AsyncMock()
    monkeypatch.setattr(reminders.bot, "send_message", sender)
    with pytest.raises(HTTPException) as error:
        await reminders.deliver_reminder(SimpleNamespace(commit=AsyncMock()), item)
    assert error.value.status_code == 429
    sender.assert_not_awaited()


async def test_settled_reminder_rejected():
    with pytest.raises(HTTPException) as error:
        await reminders.deliver_reminder(SimpleNamespace(commit=AsyncMock()), debt(status=Status.SETTLED))
    assert error.value.status_code == 409


def test_postgresql_schema_compiles():
    compiled = "\n".join(str(CreateTable(table).compile(dialect=postgresql.dialect())) for table in Base.metadata.sorted_tables)
    assert "NUMERIC(14, 2)" in compiled
    assert "ck_debt_remaining" in compiled
    assert "uq_repayment_request" in compiled


def test_reminder_uzbek_copy():
    assert "Assalomu alaykum" in reminders.reminder_text(debt(), "friendly")
    assert "Hurmatli foydalanuvchi" in reminders.reminder_text(debt(), "formal")
