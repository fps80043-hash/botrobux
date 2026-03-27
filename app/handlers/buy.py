from __future__ import annotations

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message

from app.keyboards.inline import confirm_purchase_keyboard, back_home
from app.services.site_api import site_api
from app.utils.formatters import money

router = Router()


class BuyState(StatesGroup):
    waiting_nickname = State()
    waiting_email = State()


@router.callback_query(F.data.startswith('buy:pick:'))
async def buy_pick(callback: CallbackQuery, state: FSMContext) -> None:
    package_id = int(callback.data.split(':')[-1])
    packages = await site_api.packages()
    package = next((item for item in packages if int(item.get('id', 0)) == package_id), None)
    if not package:
        await callback.answer('Пакет не найден', show_alert=True)
        return
    await state.update_data(package_id=package_id, package=package)
    await state.set_state(BuyState.waiting_nickname)
    title = package.get('title') or f"{package.get('robux_amount', 0)} Robux"
    text = (
        '<b>🛒 Оформление заказа</b>\n\n'
        f'Пакет: <b>{title}</b>\n'
        f'Цена: <b>{money(package.get("price", 0))}</b>\n\n'
        'Отправь Roblox nickname следующим сообщением.'
    )
    await callback.message.edit_text(text, reply_markup=back_home())
    await callback.answer()


@router.message(BuyState.waiting_nickname)
async def buy_nickname(message: Message, state: FSMContext) -> None:
    await state.update_data(nickname=message.text.strip())
    await state.set_state(BuyState.waiting_email)
    await message.answer(
        '<b>📧 Email для чека</b>\n\nОтправь email следующим сообщением или напиши <code>-</code>, если чек не нужен.'
    )


@router.message(BuyState.waiting_email)
async def buy_email(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    email = None if message.text.strip() == '-' else message.text.strip()
    await state.update_data(email=email)
    package = data['package']
    text = (
        '<b>🧾 Подтверждение заказа</b>\n\n'
        f'Пакет: <b>{package.get("title") or package.get("robux_amount", 0)}</b>\n'
        f'Цена: <b>{money(package.get("price", 0))}</b>\n'
        f'Nickname: <code>{data.get("nickname")}</code>\n'
        f'Email: <code>{email or "не указан"}</code>\n\n'
        'Подтверди покупку кнопкой ниже.'
    )
    await message.answer(text, reply_markup=confirm_purchase_keyboard())


@router.callback_query(F.data == 'buy:confirm')
async def buy_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        result = await site_api.create_order(
            telegram_id=callback.from_user.id,
            package_id=int(data['package_id']),
            nickname=str(data['nickname']),
            email=data.get('email'),
        )
        text = (
            '<b>✅ Заказ создан</b>\n\n'
            f'Номер заказа: <code>{result.get("order_id") or result.get("id") or "—"}</code>\n'
            f'Статус: <b>{result.get("status", "created")}</b>\n'
            f'Списано: <b>{money(result.get("charged_amount", result.get("price", 0)))}</b>'
        )
    except Exception:
        text = '⚠️ Не удалось оформить покупку. Проверь баланс, каталог пакетов и backend.'
    await state.clear()
    await callback.message.edit_text(text, reply_markup=back_home())
    await callback.answer()
