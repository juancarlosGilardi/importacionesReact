import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "importaciones_costeo")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev_secret_key_change_me")
    JWT_EXPIRATION_HOURS: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    JWT_ALGORITHM: str = "HS256"


settings = Settings()
