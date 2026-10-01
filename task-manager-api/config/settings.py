import os
from dotenv import load_dotenv

load_dotenv()


def _required_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Variável de ambiente '{name}' não definida — "
            f"copie .env.example para .env e preencha o valor."
        )
    return value


class Settings:
    SECRET_KEY = _required_env("SECRET_KEY")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")


settings = Settings()
