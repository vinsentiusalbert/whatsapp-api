import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    mywhatsapp_base_url: str = os.getenv(
        "MYWHATSAPP_BASE_URL", "https://panel.mywhatsapp.my.id"
    )
    mywhatsapp_api_key: str | None = os.getenv("MYWHATSAPP_API_KEY")
    mywhatsapp_sender: str | None = os.getenv("MYWHATSAPP_SENDER")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_name: str = os.getenv("DB_NAME", "whatsapp_db")
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")


settings = Settings()
