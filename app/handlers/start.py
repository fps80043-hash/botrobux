from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards.main import main_menu

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    text = (
        "🔥 <b>Добро пожаловать в магазин Robux</b>\n\n"
        "Здесь ты можешь быстро купить Robux, проверить баланс, посмотреть наличие и историю заказов.\n\n"
        "Для начала привяжи аккаунт сайта через кнопку ниже."
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="HTML")
