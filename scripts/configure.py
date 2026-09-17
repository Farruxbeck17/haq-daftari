import json
import secrets
from getpass import getpass
from pathlib import Path
from urllib.parse import urlparse


def prompt(label, secret=False):
    while True:
        value = getpass(label + ": ") if secret else input(label + ": ").strip()
        if value and "\n" not in value and "\r" not in value:
            return value
        print("Qiymatni kiriting.")


def main():
    root = Path(__file__).resolve().parent.parent
    target = root / ".env"
    if target.exists():
        print(".env mavjud. Uning nusxasini saqlang va kerakli qiymatlarni tahrirlang.")
        return
    token = prompt("BotFather bergan BOT_TOKEN", secret=True)
    username = prompt("Bot foydalanuvchi nomi").removeprefix("@")
    while True:
        webapp = prompt("Mini ilovaning HTTPS manzili").rstrip("/")
        parsed = urlparse(webapp)
        if parsed.scheme == "https" and parsed.netloc and not parsed.query and not parsed.fragment:
            break
        print("To'g'ri HTTPS manzilini kiriting.")
    production = input("Ishchi muhitmi? [ha/yo'q]: ").strip().lower() == "ha"
    password = secrets.token_hex(24)
    values = {
        "PROJECT_NAME": "Haq daftari", "ENVIRONMENT": "production" if production else "development",
        "BOT_TOKEN": token, "BOT_USERNAME": username, "WEBAPP_URL": webapp,
        "JWT_SECRET": secrets.token_hex(48), "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "43200", "INIT_DATA_MAX_AGE_SECONDS": "3600",
        "POSTGRES_PASSWORD": password,
        "DATABASE_URL": f"postgresql+asyncpg://qarzdaftar:{password}@127.0.0.1:5432/qarzdb",
        "AUTO_CREATE_TABLES": "false", "RUN_BOT": "true", "RUN_SCHEDULER": "true",
        "ESKIZ_EMAIL": "", "ESKIZ_PASSWORD": "", "ESKIZ_SENDER": "4546",
    }
    origin = f"{parsed.scheme}://{parsed.netloc}"
    lines = [f"{key}={json.dumps(value, ensure_ascii=False)}" for key, value in values.items()]
    lines.append("CORS_ORIGINS='" + json.dumps([origin], ensure_ascii=False) + "'")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    target.chmod(0o600)
    print(".env yaratildi. Endi docker compose up --build -d buyrug'ini bajaring.")


if __name__ == "__main__":
    main()
