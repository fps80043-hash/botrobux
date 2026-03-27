from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from app.keyboards.main import packages_keyboard
from app.services.robux_service import robux_service

router = Router()


class PurchaseState(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_email = State()


@router.message(F.text == "🛒 Купить Robux")
async def shop_handler(message: Message) -> None:
    try:
        packages = await robux_service.get_packages()
        if not packages:
            await message.answer("Сейчас нет доступных пакетов Robux.")
            return
        await message.answer(
            "<b>Выбери пакет Robux</b>",
            parse_mode="HTML",
            reply_markup=packages_keyboard(packages),
        )
    except Exception:
        await message.answer("Не удалось загрузить каталог пакетов.")


@router.callback_query(F.data.startswith("buy:"))
async def buy_package(callback: CallbackQuery, state: FSMContext) -> None:
    package_id = int(callback.data.split(":", 1)[1])
    await state.update_data(package_id=package_id)
    await state.set_state(PurchaseState.waiting_for_nickname)
    await callback.message.answer("Введи свой Roblox nickname:")
    await callback.answer()


@router.message(PurchaseState.waiting_for_nickname)
async def get_nickname(message: Message, state: FSMContext) -> None:
    await state.update_data(nickname=message.text.strip())
    await state.set_state(PurchaseState.waiting_for_email)
    await message.answer("Введи email для чека или напиши '-' если не нужен:")


@router.message(PurchaseState.waiting_for_email)
async def finish_purchase(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    email = None if message.text.strip() == "-" else message.text.strip()

    try:
        result = await robux_service.create_order(
            telegram_id=message.from_user.id,
            package_id=data["package_id"],
            nickname=data["nickname"],
            email=email,
        )
        text = (
            f"✅ <b>Заказ создан</b>\n\n"
            f"Номер заказа: <code>{result.get('order_id')}</code>\n"
            f"Статус: <b>{result.get('status', 'created')}</b>\n"
            f"Списано: <b>{result.get('charged_amount', 0)} ₽</b>\n"
            f"Остаток баланса: <b>{result.get('balance_left', 0)} ₽</b>"
        )
        await message.answer(text, parse_mode="HTML")
    except Exception:
        await message.answer("Не удалось оформить покупку. Проверь баланс, наличие Robux и backend API.")
    finally:
        await state.clear()
