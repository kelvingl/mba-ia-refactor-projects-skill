import os


def required_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} não definida — copie .env.example para .env e preencha"
        )
    return value


class Settings:
    def __init__(self):
        self.SECRET_KEY = required_env("SECRET_KEY")
        self.DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
        self.DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///tasks.db")
        self.SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
        self.SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
        self.SMTP_USER = os.environ.get("SMTP_USER", "")
        self.SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")


settings = Settings()
