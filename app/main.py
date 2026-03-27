import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.handlers.start import router as start_router
from app.handlers.profile import router as profile_router
from app.handlers.stock import router as stock_router
from app.handlers.orders import router as orders_router
from app.handlers.link import router as link_router
from app.handlers.shop import router as shop_router
from app.services.api_client import api_client


async def main() -> None:
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")
    if not settings.api_base_url:
        raise RuntimeError("API_BASE_URL is not set")

    logging.basicConfig(level=logging.INFO)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(profile_router)
    dp.include_router(stock_router)
    dp.include_router(orders_router)
    dp.include_router(link_router)
    dp.include_router(shop_router)

    try:
        await dp.start_polling(bot)
    finally:
        await api_client.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
