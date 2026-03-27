from aiogram import Router, F
from aiogram.types import Message

from app.services.robux_service import robux_service

router = Router()


@router.message(F.text == "👤 Профиль")
async def profile_handler(message: Message) -> None:
    try:
        profile = await robux_service.get_profile(message.from_user.id)
        text = (
            f"<b>Профиль</b>\n\n"
            f"ID: <code>{profile.get('id', '-')}</code>\n"
            f"Логин: <b>{profile.get('username', 'Не привязан')}</b>\n"
            f"Баланс: <b>{profile.get('balance', 0)} {profile.get('currency', 'RUB')}</b>\n"
            f"Привязка: <b>{'Да' if profile.get('is_linked') else 'Нет'}</b>"
        )
    except Exception:
        text = "Не удалось получить профиль. Скорее всего аккаунт ещё не привязан. Нажми «🔗 Привязать аккаунт»."

    await message.answer(text, parse_mode="HTML")
