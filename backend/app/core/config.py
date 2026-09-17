from functools import lru_cache
from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "Haq daftari"
    BOT_TOKEN: str
    BOT_USERNAME: str
    WEBAPP_URL: str
    DATABASE_URL: str
    JWT_SECRET: str = Field(min_length=32)
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=43200, ge=1, le=43200)
    INIT_DATA_MAX_AGE_SECONDS: int = Field(default=3600, ge=60, le=86400)
    ESKIZ_EMAIL: str = ""
    ESKIZ_PASSWORD: str = ""
    ESKIZ_SENDER: str = "4546"
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    AUTO_CREATE_TABLES: bool = True
    RUN_BOT: bool = True
    RUN_SCHEDULER: bool = True

    @field_validator("DATABASE_URL")
    @classmethod
    def database_url(cls, value: str) -> str:
        if value.startswith("postgresql://"):
            value = "postgresql+asyncpg://" + value.removeprefix("postgresql://")
        if not value.startswith("postgresql+asyncpg://"):
            raise ValueError("PostgreSQL va asyncpg manzili talab qilinadi")
        return value

    @field_validator("BOT_USERNAME")
    @classmethod
    def username(cls, value: str) -> str:
        value = value.removeprefix("@")
        if not value.replace("_", "").isalnum():
            raise ValueError("Bot foydalanuvchi nomi noto'g'ri")
        return value

    @model_validator(mode="after")
    def production(self):
        if urlparse(self.WEBAPP_URL).scheme != "https":
            raise ValueError("Mini ilova manzili HTTPS bo'lishi kerak")
        if self.ENVIRONMENT == "production":
            if "*" in self.CORS_ORIGINS or not self.CORS_ORIGINS:
                raise ValueError("Ishchi muhitda aniq CORS manzillarini kiriting")
            if self.AUTO_CREATE_TABLES:
                raise ValueError("Ishchi muhitda Alembic migratsiyalaridan foydalaning")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
