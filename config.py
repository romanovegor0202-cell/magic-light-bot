import os
from dataclasses import dataclass
from pathlib import Path


def _load_local_env():
    """Load a simple local .env file without requiring python-dotenv.

    BotHost supplies environment variables itself, so existing environment
    values always take priority. This also keeps local Windows запуск working.
    """
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("\"", "'"):
                value = value[1:-1]
            if key:
                os.environ.setdefault(key, value)
    except OSError:
        pass


_load_local_env()


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
        raise RuntimeError("BOT_TOKEN не указан в .env или переменных окружения")
    if not manager_id_raw:
        raise RuntimeError("MANAGER_ID не указан в .env или переменных окружения")
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
