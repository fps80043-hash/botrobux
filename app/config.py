from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _get_optional_int(name: str) -> int | None:
    value = os.getenv(name, '').strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    api_base_url: str = os.getenv("API_BASE_URL", "")
    api_secret: str = os.getenv("API_SECRET", "")
    start_image_url: str = os.getenv("START_IMAGE_URL", "")
    test_site_user_id: int | None = _get_optional_int("TEST_SITE_USER_ID")


settings = Settings()
