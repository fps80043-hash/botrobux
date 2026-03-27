from aiogram import Router, F
from aiogram.types import Message

from app.services.robux_service import robux_service

router = Router()


@router.message(F.text == "📦 Наличие")
async def stock_handler(message: Message) -> None:
    try:
        stock = await robux_service.get_stock()
        text = (
            f"<b>Наличие Robux</b>\n\n"
            f"Доступно Robux: <b>{stock.get('available_robux', 0)}</b>\n"
            f"Доступно пакетов: <b>{stock.get('available_packages', 0)}</b>\n"
            f"Статус: <b>{stock.get('status', 'unknown')}</b>"
        )
    except Exception:
        text = "Не удалось получить наличие. Проверь backend API."

    await message.answer(text, parse_mode="HTML")
