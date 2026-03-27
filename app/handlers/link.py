from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from app.services.robux_service import robux_service

router = Router()


class LinkState(StatesGroup):
    waiting_for_code = State()


@router.message(F.text == "🔗 Привязать аккаунт")
async def ask_link_code(message: Message, state: FSMContext) -> None:
    await state.set_state(LinkState.waiting_for_code)
    await message.answer(
        "Пришли код привязки, который сайт показал в личном кабинете.\nПример: <code>RBX-483912</code>",
        parse_mode="HTML",
    )


@router.message(LinkState.waiting_for_code)
async def process_link_code(message: Message, state: FSMContext) -> None:
    code = message.text.strip()
    try:
        result = await robux_service.link_account(message.from_user.id, code)
        await message.answer(result.get("message", "Аккаунт успешно привязан."))
    except Exception:
        await message.answer("Код не подошёл или backend вернул ошибку.")
    finally:
        await state.clear()
