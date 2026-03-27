from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    api_base_url: str = os.getenv("API_BASE_URL", "")
    api_secret: str = os.getenv("API_SECRET", "")
    start_image_url: str = os.getenv("START_IMAGE_URL", "")

settings = Settings()
