import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException
from jose import jwt
from pydantic import ValidationError

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token, verify_telegram_init_data
from app.schemas.transaction import RepaymentCreate, TransactionCreate


def signed_data(values=None):
    data = {"auth_date": str(int(time.time())),
            "user": json.dumps({"id": 987654321, "first_name": "O'tkir"}, separators=(",", ":")),
            "query_id": "test-query"}
    if values:
        data.update(values)
    secret = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
    content = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
    data["hash"] = hmac.new(secret, content.encode(), hashlib.sha256).hexdigest()
    return urlencode(data)


def test_valid_telegram_signature():
    assert verify_telegram_init_data(signed_data(), settings.BOT_TOKEN)["id"] == 987654321


@pytest.mark.parametrize("data", [
    "",
    "hash=abc",
    signed_data() + "&auth_date=123",
    signed_data().replace("test-query", "changed-query"),
    signed_data({"auth_date": str(int(time.time()) - 7200)}),
    signed_data({"auth_date": str(int(time.time()) + 3600)}),
    signed_data({"user": "[]"}),
    signed_data({"user": '{"id": true, "first_name": "Ism"}'}),
    signed_data({"user": '{"id": -1, "first_name": "Ism"}'}),
    signed_data({"user": '{"id": 5, "first_name": "Bot", "is_bot": true}'}),
])
def test_invalid_init_data_is_rejected(data):
    with pytest.raises(HTTPException) as error:
        verify_telegram_init_data(data, settings.BOT_TOKEN)
    assert error.value.status_code == 401


def test_wrong_bot_token():
    with pytest.raises(HTTPException):
        verify_telegram_init_data(signed_data(), "wrong-token")


def test_jwt_round_trip():
    token = create_access_token({"sub": "42"})
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["exp"] > payload["iat"]


@pytest.mark.parametrize("payload", [
    {"sub": "42", "exp": 1, "iat": 0, "aud": "qarzdaftar-miniapp", "iss": "qarzdaftar"},
    {"sub": "42", "iat": int(time.time()), "aud": "qarzdaftar-miniapp", "iss": "qarzdaftar"},
    {"sub": "-1", "iat": int(time.time()), "exp": int(time.time()) + 1000, "aud": "qarzdaftar-miniapp", "iss": "qarzdaftar"},
])
def test_invalid_jwt(payload):
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    with pytest.raises(HTTPException):
        decode_access_token(token)


@pytest.mark.parametrize("amount", ["0", "-1", "0.001", "1000000000000", "NaN", "Infinity"])
def test_invalid_amounts(amount):
    with pytest.raises(ValidationError):
        TransactionCreate(counterparty_name="Ali", type="GIVEN", amount=amount)


def test_decimal_money_is_exact():
    debt = TransactionCreate(counterparty_name="Ali", type="GIVEN", amount="0.10")
    assert str(debt.amount + debt.amount + debt.amount) == "0.30"


def test_whitespace_name_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(counterparty_name="  ", type="GIVEN", amount="10")


def test_foreign_currency_rejected():
    with pytest.raises(ValidationError):
        TransactionCreate(counterparty_name="Ali", type="GIVEN", amount="10", currency="USD")


def test_phone_and_repayment_key_validation():
    with pytest.raises(ValidationError):
        TransactionCreate(counterparty_name="Ali", type="GIVEN", amount="10", counterparty_phone="+123")
    with pytest.raises(ValidationError):
        RepaymentCreate(amount="10", idempotency_key="invalid")
