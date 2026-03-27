from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery, ReplyKeyboardRemove

from app.config import settings
from app.keyboards.inline import main_menu
from app.repositories.state_repo import state_repo
from app.services.site_api import site_api

router = Router()


@router.callback_query(F.data == 'terms:accept')
async def accept_terms(callback: CallbackQuery) -> None:
    state_repo.accept_terms(callback.from_user.id, settings.terms_version)
    try:
        await callback.message.delete()
    except Exception:
        pass
    is_admin = await site_api.is_admin(callback.from_user.id)
    await callback.message.answer(
        '<b>✅ Соглашение принято</b>\n\nДобро пожаловать в главное меню.',
        reply_markup=main_menu(is_admin=is_admin),
    )
    await callback.answer('Готово ✨')
