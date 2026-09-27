import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-change-me"
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")

settings = Settings()
