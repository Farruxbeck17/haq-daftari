from pydantic import BaseModel, ConfigDict, Field


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(min_length=1, max_length=16384)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    phone_number: str | None
    preferred_currency: str
    sms_balance: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
