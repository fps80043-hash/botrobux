from __future__ import annotations

from app.utils.tg import safe_edit_or_send
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message

from app.keyboards.inline import (
    admin_menu,
    admin_prices_keyboard,
    admin_stock_keyboard,
    admin_gif_keyboard,
    admin_user_keyboard,
)
from app.repositories.state_repo import state_repo
from app.services.site_api import site_api
from app.utils.formatters import money

router = Router()


class AdminState(StatesGroup):
    waiting_new_price = State()
    waiting_new_stock = State()
    waiting_gif = State()
    waiting_user_query = State()
    waiting_new_balance = State()


def _not_admin() -> str:
    return '⛔ У тебя нет доступа к админке.'


@router.callback_query(F.data.startswith('admin:'))
async def admin_guard(callback: CallbackQuery) -> None:
    if callback.data == 'admin:home':
        if not await site_api.is_admin(callback.from_user.id):
            await callback.answer(_not_admin(), show_alert=True)
            return
        text = (
            '<b>🛠 Админка RBX-ST</b>\n\n'
            'Базовое управление магазином прямо из Telegram.\n\n'
            'Что уже есть:\n'
            '• просмотр конфигурации\n'
            '• изменение цены за 1 Robux\n'
            '• изменение остатка\n'
            '• поиск пользователя\n'
            '• правка стартовой GIF'
        )
        await safe_edit_or_send(callback, text, reply_markup=admin_menu())
        await callback.answer()


@router.callback_query(F.data == 'admin:prices')
async def admin_prices(callback: CallbackQuery) -> None:
    if not await site_api.is_admin(callback.from_user.id):
        await callback.answer(_not_admin(), show_alert=True)
        return
    try:
        config = await site_api.admin_get_config()
        price = config.get('price_per_robux') or config.get('robux_price') or 'не найдено'
        text = f'<b>💸 Цены</b>\n\nТекущая цена за 1 Robux: <b>{price}</b>'
    except Exception:
        text = '<b>💸 Цены</b>\n\nBackend ещё не отдаёт admin config endpoint.'
    await safe_edit_or_send(callback, text, reply_markup=admin_prices_keyboard())
    await callback.answer()


@router.callback_query(F.data == 'admin:set_price')
async def admin_set_price_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not await site_api.is_admin(callback.from_user.id):
        await callback.answer(_not_admin(), show_alert=True)
        return
    await state.set_state(AdminState.waiting_new_price)
    await callback.message.answer('Отправь новую цену за <b>1 Robux</b> следующим сообщением. Пример: <code>1.75</code>')
    await callback.answer()


@router.message(AdminState.waiting_new_price)
async def admin_set_price_finish(message: Message, state: FSMContext) -> None:
    try:
        price = float(message.text.replace(',', '.').strip())
        result = await site_api.admin_set_price(price)
        await message.answer(f'✅ Цена обновлена. Ответ backend: <code>{result}</code>')
    except Exception:
        await message.answer('⚠️ Не удалось обновить цену. Проверь admin endpoint на сайте.')
    finally:
        await state.clear()


@router.callback_query(F.data == 'admin:stock')
async def admin_stock(callback: CallbackQuery) -> None:
    if not await site_api.is_admin(callback.from_user.id):
        await callback.answer(_not_admin(), show_alert=True)
        return
    try:
        stock = await site_api.admin_get_stock()
        amount = stock.get('available_robux') or stock.get('robux') or stock.get('stock') or 0
        text = f'<b>📦 Остаток</b>\n\nТекущий остаток Robux: <b>{amount}</b>'
    except Exception:
        text = '<b>📦 Остаток</b>\n\nBackend ещё не отдаёт admin stock endpoint.'
    await safe_edit_or_send(callback, text, reply_markup=admin_stock_keyboard())
    await callback.answer()


@router.callback_query(F.data == 'admin:set_stock')
async def admin_set_stock_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not await site_api.is_admin(callback.from_user.id):
        await callback.answer(_not_admin(), show_alert=True)
        return
    await state.set_state(AdminState.waiting_new_stock)
    await callback.message.answer('Отправь новый общий остаток Robux следующим сообщением. Пример: <code>250000</code>')
    await callback.answer()


@router.message(AdminState.waiting_new_stock)
async def admin_set_stock_finish(message: Message, state: FSMContext) -> None:
    try:
        amount = int(message.text.strip())
        result = await site_api.admin_set_stock(amount)
        await message.answer(f'✅ Остаток обновлён. Ответ backend: <code>{result}</code>')
    except Exception:
        await message.answer('⚠️ Не удалось обновить остаток. Проверь admin endpoint на сайте.')
    finally:
        await state.clear()


@router.callback_query(F.data == 'admin:orders')
async def admin_orders(callback: CallbackQuery) -> None:
    if not await site_api.is_admin(callback.from_user.id):
        await callback.answer(_not_admin(), show_alert=True)
        return
    try:
        orders = await site_api.admin_orders()
        if not orders:
            text = '<b>📜 Последние заказы</b>\n\nПока пусто.'
        else:
            lines = ['<b>📜 Последние заказы</b>', '']
            for item in orders[:10]:
                oid = item.get('id') or item.get('order_id') or '—'
                title = item.get('title') or item.get('nickname') or 'Robux'
                price = item.get('price') or item.get('amount') or 0
                status = item.get('status') or 'new'
                lines.append(f'• <b>#{oid}</b> · {title} · {money(price)} · <i>{status}</i>')
            text = '\n'.join(lines)
    except Exception:
        text = '<b>📜 Последние заказы</b>\n\nBackend ещё не отдаёт admin orders endpoint.'
    await safe_edit_or_send(callback, text, reply_markup=admin_menu())
    await callback.answer()


@router.callback_query(F.data == 'admin:user')
async def admin_user(callback: CallbackQuery, state: FSMContext) -> None:
    if not await site_api.is_admin(callback.from_user.id):
        await callback.answer(_not_admin(), show_alert=True)
        return
    await state.set_state(AdminState.waiting_user_query)
    await callback.message.edit_text(
        '<b>👤 Поиск пользователя</b>\n\nОтправь email, username или ID следующим сообщением.',
        reply_markup=admin_user_keyboard(),
    )
    await callback.answer()


@router.message(AdminState.waiting_user_query)
async def admin_user_query(message: Message, state: FSMContext) -> None:
    query = message.text.strip()
    try:
        result = await site_api.admin_find_user(query)
        user = result.get('user') if isinstance(result, dict) and isinstance(result.get('user'), dict) else result
        if not isinstance(user, dict):
            raise ValueError('user not found')
        await state.update_data(found_user_id=int(user.get('id')))
        text = (
            '<b>👤 Пользователь найден</b>\n\n'
            f'ID: <code>{user.get("id")}</code>\n'
            f'Логин: <b>{user.get("username") or user.get("email") or "—"}</b>\n'
            f'Баланс: <b>{money(user.get("balance", 0))}</b>\n\n'
            'Теперь можно изменить баланс кнопкой ниже.'
        )
        await message.answer(text, reply_markup=admin_user_keyboard())
    except Exception:
        await message.answer('⚠️ Не удалось найти пользователя. Проверь admin endpoint на сайте.')
        await state.clear()


@router.callback_query(F.data == 'admin:set_balance')
async def admin_set_balance_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not await site_api.is_admin(callback.from_user.id):
        await callback.answer(_not_admin(), show_alert=True)
        return
    data = await state.get_data()
    if not data.get('found_user_id'):
        await callback.answer('Сначала найди пользователя.', show_alert=True)
        return
    await state.set_state(AdminState.waiting_new_balance)
    await callback.message.answer('Отправь новый баланс следующим сообщением. Пример: <code>1500</code>')
    await callback.answer()


@router.message(AdminState.waiting_new_balance)
async def admin_set_balance_finish(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    try:
        user_id = int(data['found_user_id'])
        balance = float(message.text.replace(',', '.').strip())
        result = await site_api.admin_set_balance(user_id, balance)
        await message.answer(f'✅ Баланс обновлён. Ответ backend: <code>{result}</code>')
    except Exception:
        await message.answer('⚠️ Не удалось обновить баланс. Проверь admin endpoint на сайте.')
    finally:
        await state.clear()


@router.callback_query(F.data == 'admin:gif')
async def admin_gif(callback: CallbackQuery) -> None:
    if not await site_api.is_admin(callback.from_user.id):
        await callback.answer(_not_admin(), show_alert=True)
        return
    current = state_repo.get_setting('start_gif') or 'не задана'
    text = (
        '<b>🖼 Стартовая GIF</b>\n\n'
        f'Текущее значение: <code>{current}</code>\n\n'
        'Сюда можно сохранить Telegram <b>file_id</b> анимации или прямую ссылку.'
    )
    await safe_edit_or_send(callback, text, reply_markup=admin_gif_keyboard())
    await callback.answer()


@router.callback_query(F.data == 'admin:set_gif')
async def admin_set_gif_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not await site_api.is_admin(callback.from_user.id):
        await callback.answer(_not_admin(), show_alert=True)
        return
    await state.set_state(AdminState.waiting_gif)
    await callback.message.answer('Отправь новый GIF file_id или ссылку следующим сообщением.')
    await callback.answer()


@router.message(AdminState.waiting_gif)
async def admin_set_gif_finish(message: Message, state: FSMContext) -> None:
    value = message.text.strip()
    state_repo.set_setting('start_gif', value)
    await message.answer('✅ Стартовая GIF обновлена.')
    await state.clear()
