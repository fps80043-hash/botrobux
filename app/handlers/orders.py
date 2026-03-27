from aiogram import Router, F
from aiogram.types import Message

from app.services.robux_service import robux_service

router = Router()


@router.message(F.text == "📜 Мои заказы")
async def orders_handler(message: Message) -> None:
    try:
        orders = await robux_service.get_orders(message.from_user.id)
        if not orders:
            await message.answer("У тебя пока нет заказов.")
            return

        lines = ["<b>Последние заказы</b>\n"]
        for item in orders[:10]:
            lines.append(
                f"• <b>#{item.get('id')}</b> | {item.get('title', 'Robux')} | {item.get('price', 0)} ₽ | {item.get('status', 'new')}"
            )
        await message.answer("\n".join(lines), parse_mode="HTML")
    except Exception:
        await message.answer("Не удалось загрузить историю заказов.")
