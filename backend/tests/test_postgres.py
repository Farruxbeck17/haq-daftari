import asyncio
import os
from datetime import timedelta
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models import DebtTransaction, RepaymentHistory, TransactionStatus, User
from app.services.ledger import today

TEST_URL = os.getenv("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not TEST_URL, reason="Alohida PostgreSQL sinov bazasi berilmagan")


@pytest_asyncio.fixture
async def database():
    url = make_url(TEST_URL)
    if not url.database or not url.database.endswith("_test"):
        pytest.fail("Sinov bazasining nomi _test bilan tugashi kerak")
    engine = create_async_engine(TEST_URL)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as db:
        users = [User(telegram_id=value, first_name=f"Ism {value}") for value in [101, 202, 303]]
        db.add_all(users)
        await db.commit()
        ids = [user.id for user in users]
    async def override_db():
        async with session_factory() as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    try:
        yield session_factory, ids
    finally:
        app.dependency_overrides.clear()
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()


def headers(user_id):
    return {"Authorization": "Bearer " + create_access_token({"sub": str(user_id)})}


async def create(client, user_id, **changes):
    body = {"counterparty_name": "Vali", "type": "GIVEN", "amount": "100.00",
            "due_date": str(today() - timedelta(days=1))}
    body.update(changes)
    response = await client.post("/api/v1/transactions", headers=headers(user_id), json=body)
    assert response.status_code == 201, response.text
    return response.json()


async def test_visibility_and_overpayment(database):
    factory, ids = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        item = await create(client, ids[0])
        outsider = await client.get("/api/v1/transactions/" + item["id"], headers=headers(ids[2]))
        assert outsider.status_code == 404
        overpay = await client.post("/api/v1/transactions/" + item["id"] + "/repay", headers=headers(ids[0]),
                                   json={"amount": "100.01", "idempotency_key": str(uuid4())})
        assert overpay.status_code == 422
        dashboard = await client.get("/api/v1/dashboard", headers=headers(ids[0]))
        assert dashboard.json()["total_receivable"] == 100
        assert dashboard.json()["overdue_count"] == 1


async def test_repayment_retry_and_conflict(database):
    factory, ids = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        item = await create(client, ids[0])
        path = "/api/v1/transactions/" + item["id"] + "/repay"
        payload = {"amount": "40.00", "idempotency_key": str(uuid4()), "note": ""}
        first = await client.post(path, headers=headers(ids[0]), json=payload)
        second = await client.post(path, headers=headers(ids[0]), json=payload)
        assert first.status_code == second.status_code == 200
        assert second.json()["remaining_amount"] == "60.00"
        assert len(second.json()["repayments"]) == 1
        payload["amount"] = "20"
        assert (await client.post(path, headers=headers(ids[0]), json=payload)).status_code == 409


async def test_concurrent_repayments_cannot_overpay(database):
    factory, ids = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        item = await create(client, ids[0])
        async def pay():
            return await client.post("/api/v1/transactions/" + item["id"] + "/repay", headers=headers(ids[0]),
                                     json={"amount": "70", "idempotency_key": str(uuid4())})
        results = await asyncio.gather(pay(), pay())
        assert sorted(result.status_code for result in results) == [200, 422]
        detail = await client.get("/api/v1/transactions/" + item["id"], headers=headers(ids[0]))
        assert detail.json()["remaining_amount"] == "30.00"


async def test_shared_taken_balances_and_permissions(database):
    factory, ids = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        item = await create(client, ids[0], type="TAKEN", share_with_telegram=True)
        assert item["confirmation_link"]
        before = await client.get("/api/v1/dashboard", headers=headers(ids[0]))
        assert before.json()["active_count"] == 0
        async with factory() as db:
            debt = await db.get(DebtTransaction, UUID(item["id"]))
            debt.counterparty_id = ids[1]
            debt.status = TransactionStatus.ACTIVE
            await db.commit()
        creditor = await client.get("/api/v1/dashboard", headers=headers(ids[1]))
        debtor = await client.get("/api/v1/dashboard", headers=headers(ids[0]))
        assert creditor.json()["total_receivable"] == debtor.json()["total_payable"] == 100
        path = "/api/v1/transactions/" + item["id"] + "/repay"
        payload = {"amount": "100", "idempotency_key": str(uuid4())}
        assert (await client.post(path, headers=headers(ids[0]), json=payload)).status_code == 403
        paid = await client.post(path, headers=headers(ids[1]), json=payload)
        assert paid.status_code == 200, paid.text
        assert paid.json()["status"] == "SETTLED"
        settled = await client.get("/api/v1/transactions?tab=settled", headers=headers(ids[0]))
        assert len(settled.json()) == 1
        async with factory() as db:
            assert len((await db.scalars(select(RepaymentHistory))).all()) == 1

async def test_confirmation_maps_internal_id_and_is_single_use(database, monkeypatch):
    from datetime import datetime, timezone
    from unittest.mock import AsyncMock
    from aiogram.types import CallbackQuery, Chat, Message, User as TelegramUser
    from app.bot.handlers import callback as handler

    factory, ids = database
    monkeypatch.setattr(handler, "SessionLocal", factory)
    monkeypatch.setattr(CallbackQuery, "answer", AsyncMock())
    monkeypatch.setattr(Message, "edit_text", AsyncMock())
    sender = AsyncMock()
    monkeypatch.setattr(handler.bot, "send_message", sender)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        item = await create(client, ids[0], share_with_telegram=True)
        async with factory() as db:
            debt = await db.get(DebtTransaction, UUID(item["id"]))
            token = debt.confirmation_token
        def query(telegram_id, action):
            return CallbackQuery(id=str(uuid4()), from_user=TelegramUser(id=telegram_id, first_name="Vali", is_bot=False),
                chat_instance="test", message=Message(message_id=1, date=datetime.now(timezone.utc),
                chat=Chat(id=telegram_id, type="private"), text="Tasdiqlash"), data=f"{action}:{token}")
        await handler.confirm_or_reject(query(101, "confirm"))
        async with factory() as db:
            debt = await db.get(DebtTransaction, UUID(item["id"]))
            assert debt.status == TransactionStatus.PENDING_CONFIRMATION
        await handler.confirm_or_reject(query(202, "confirm"))
        await handler.confirm_or_reject(query(303, "reject"))
        async with factory() as db:
            debt = await db.get(DebtTransaction, UUID(item["id"]))
            assert debt.status == TransactionStatus.ACTIVE
            assert debt.counterparty_id == ids[1]
            assert debt.counterparty_id != 202
        sender.assert_awaited_once()


async def test_concurrent_reminders_share_cooldown(database, monkeypatch):
    from unittest.mock import AsyncMock
    from app.services import reminder_engine

    factory, ids = database
    sender = AsyncMock()
    monkeypatch.setattr(reminder_engine.bot, "send_message", sender)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        item = await create(client, ids[0])
        async with factory() as db:
            debt = await db.get(DebtTransaction, UUID(item["id"]))
            debt.counterparty_id = ids[1]
            await db.commit()
        async def remind():
            return await client.post("/api/v1/transactions/" + item["id"] + "/send-reminder",
                                     headers=headers(ids[0]), json={"tone": "formal"})
        results = await asyncio.gather(remind(), remind())
        assert sorted(result.status_code for result in results) == [200, 429]
        sender.assert_awaited_once()

async def test_auth_upsert_and_unauthenticated_access(database):
    from test_security import signed_data
    factory, ids = database
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/api/v1/dashboard")).status_code == 401
        payload = {"init_data": signed_data()}
        responses = await asyncio.gather(
            client.post("/api/v1/auth/telegram", json=payload),
            client.post("/api/v1/auth/telegram", json=payload))
        assert all(response.status_code == 200 for response in responses)
        assert responses[0].json()["user"]["id"] == responses[1].json()["user"]["id"]
        token = responses[0].json()["access_token"]
        dashboard = await client.get("/api/v1/dashboard", headers={"Authorization": "Bearer " + token})
        assert dashboard.status_code == 200
        assert dashboard.json()["active_count"] == 0

