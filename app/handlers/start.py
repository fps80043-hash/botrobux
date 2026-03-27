from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardRemove

from app.config import settings
from app.keyboards.inline import terms_keyboard, main_menu
from app.repositories.state_repo import state_repo
from app.services.site_api import site_api
from app.ui.texts import TERMS_TEXT, welcome_caption

router = Router()


async def _send_start(message: Message) -> None:
    await message.answer('✨ Обновляю интерфейс...', reply_markup=ReplyKeyboardRemove())
    gif = state_repo.get_setting('start_gif') or settings.default_start_gif
    caption = welcome_caption(settings.test_site_user_id is not None, settings.test_site_user_id)
    caption += f'\n\n<blockquote>build: {settings.build_tag}</blockquote>'

    if gif:
        await message.answer_animation(animation=gif, caption=caption)
    else:
        await message.answer(caption)

    if state_repo.has_accepted_terms(message.from_user.id, settings.terms_version):
        is_admin = await site_api.is_admin(message.from_user.id)
        await message.answer(
            '<b>🏠 Главное меню</b>\n\nВыбирай нужный раздел ниже 👇',
            reply_markup=main_menu(is_admin=is_admin),
        )
        return

    await message.answer(TERMS_TEXT, reply_markup=terms_keyboard())


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await _send_start(message)


@router.message(Command('menu'))
async def menu_handler(message: Message) -> None:
    is_admin = await site_api.is_admin(message.from_user.id)
    await message.answer('🏠 Возвращаю в главное меню.', reply_markup=ReplyKeyboardRemove())
    await message.answer('<b>🏠 Главное меню</b>\n\nВыбирай нужный раздел ниже 👇', reply_markup=main_menu(is_admin=is_admin))
