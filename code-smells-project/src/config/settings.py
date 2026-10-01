import os
from dotenv import load_dotenv

load_dotenv()


def _required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} não definida — copie .env.example para .env e preencha"
        )
    return value


class Settings:
    SECRET_KEY: str = _required_env("SECRET_KEY")
    DEBUG: bool = os.environ.get("FLASK_DEBUG", "0") == "1"
    DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "loja.db")


settings = Settings()
