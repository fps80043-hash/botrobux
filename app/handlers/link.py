from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from app.config import settings
from app.services.site_api import site_api

router = Router()


class LinkState(StatesGroup):
    waiting_code = State()


@router.message(LinkState.waiting_code)
async def receive_link_code(message: Message, state: FSMContext) -> None:
    if settings.test_site_user_id is not None:
        await message.answer(f'✅ Тестовая привязка уже активна: ID сайта <code>{settings.test_site_user_id}</code>')
        await state.clear()
        return

    code = message.text.strip()
    try:
        result = await site_api.link_account(message.from_user.id, code)
        await message.answer(result.get('message', '✅ Аккаунт успешно привязан.'))
    except Exception:
        await message.answer('⚠️ Код не подошёл или backend вернул ошибку.')
    finally:
        await state.clear()
