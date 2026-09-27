import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-only-change-me')
    DEBUG: bool = os.environ.get('FLASK_DEBUG', '0') == '1'
    DATABASE_URL: str = os.environ.get('DATABASE_URL', 'sqlite:///tasks.db')
    SMTP_HOST: str = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.environ.get('SMTP_PORT', '587'))
    SMTP_USER: str = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD: str = os.environ.get('SMTP_PASSWORD', '')


settings = Settings()
