import os

os.environ.setdefault("BOT_TOKEN", "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
os.environ.setdefault("BOT_USERNAME", "qarzdaftar_test_bot")
os.environ.setdefault("WEBAPP_URL", "https://qarzdaftar.example")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/qarzdaftar_test")
os.environ.setdefault("JWT_SECRET", "qarzdaftar-test-secret-used-only-in-automated-tests")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("RUN_BOT", "false")
os.environ.setdefault("RUN_SCHEDULER", "false")
