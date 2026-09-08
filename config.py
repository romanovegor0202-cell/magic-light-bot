import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str
    manager_id: int
    manager_username: str
    manager_phone: str
    company_name: str


def get_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    manager_id_raw = os.getenv("MANAGER_ID", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN не указан в .env")
    if not manager_id_raw:
        raise RuntimeError("MANAGER_ID не указан в .env")
    try:
        manager_id = int(manager_id_raw)
    except ValueError as exc:
        raise RuntimeError("MANAGER_ID должен быть числом") from exc
    return Settings(
        bot_token=token,
        manager_id=manager_id,
        manager_username=os.getenv("MANAGER_USERNAME", "").strip().lstrip("@"),
        manager_phone=os.getenv("MANAGER_PHONE", "").strip(),
        company_name=os.getenv("COMPANY_NAME", "Magic Light").strip() or "Magic Light",
    )
