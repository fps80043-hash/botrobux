
from __future__ import annotations

from app.utils.tg import safe_edit_or_send
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.keyboards.inline import main_menu, back_home, packages_keyboard
from app.services.site_api import site_api
from app.utils.formatters import money, yes_no

router = Router()


async def _home_text(callback: CallbackQuery) -> str:
    try:
        balance_data = await site_api.balance(callback.from_user.id)
    except Exception:
        balance_data = {'balance': 0}
    try:
        stock = await site_api.stock()
    except Exception:
        stock = {'available_robux': 0}
    balance_value = balance_data.get('balance', 0)
    return (
        '<b>🏠 Главное меню RBX-ST</b>

'
        f'💳 Баланс: <b>{money(balance_value)}</b>
'
        f'📦 Наличие: <b>{stock.get("available_robux", 0)}</b> Robux
'
        '⚡ Всё управление теперь через inline-кнопки.'
    )


@router.callback_query(F.data == 'menu:home')
async def menu_home(callback: CallbackQuery) -> None:
    is_admin = await site_api.is_admin(callback.from_user.id)
    text = await _home_text(callback)
    await safe_edit_or_send(callback, text, reply_markup=main_menu(is_admin=is_admin))
    await callback.answer()


@router.callback_query(F.data == 'menu:profile')
async def menu_profile(callback: CallbackQuery) -> None:
    try:
        profile = await site_api.profile(callback.from_user.id)
        text = (
            '<b>👤 Профиль</b>

'
            f'🆔 ID: <code>{profile.get("id", "-")}</code>
'
            f'🧷 Логин: <b>{profile.get("username") or profile.get("email") or "Не привязан"}</b>
'
            f'💳 Баланс: <b>{money(profile.get("balance", 0))}</b>
'
            f'⭐ Premium: <b>{yes_no(profile.get("premium") or profile.get("premium_until"))}</b>
'
            f'🛡 Админ: <b>{yes_no(profile.get("is_admin"))}</b>'
        )
    except Exception:
        text = '⚠️ Не удалось получить профиль. Возможно, аккаунт ещё не привязан к сайту.'
    await safe_edit_or_send(callback, text, reply_markup=back_home())
    await callback.answer()


@router.callback_query(F.data == 'menu:balance')
async def menu_balance(callback: CallbackQuery) -> None:
    try:
        balance_data = await site_api.balance(callback.from_user.id)
        text = (
            '<b>💳 Баланс</b>

'
            f'Текущий баланс: <b>{money(balance_data.get("balance", 0))}</b>
'
            f'Валюта: <b>{balance_data.get("currency", "RUB")}</b>'
        )
    except Exception:
        text = '⚠️ Не удалось загрузить баланс.'
    await safe_edit_or_send(callback, text, reply_markup=back_home())
    await callback.answer()


@router.callback_query(F.data == 'menu:stock')
async def menu_stock(callback: CallbackQuery) -> None:
    try:
        stock = await site_api.stock()
        text = (
            '<b>📦 Наличие Robux</b>

'
            f'Доступно Robux: <b>{stock.get("available_robux", 0)}</b>
'
            f'Доступно пакетов: <b>{stock.get("available_packages", 0)}</b>
'
            f'Статус: <b>{stock.get("status", "unknown")}</b>'
        )
    except Exception:
        text = '⚠️ Не удалось получить наличие.'
    await safe_edit_or_send(callback, text, reply_markup=back_home())
    await callback.answer()


@router.callback_query(F.data == 'menu:orders')
async def menu_orders(callback: CallbackQuery) -> None:
    try:
        orders = await site_api.orders(callback.from_user.id, limit=10)
        if not orders:
            text = '<b>📜 Мои заказы</b>

Заказов пока нет.'
        else:
            lines = ['<b>📜 Последние заказы</b>', '']
            for item in orders[:10]:
                title = item.get('title') or item.get('type') or 'Robux'
                status = item.get('status') or item.get('state') or 'new'
                price = item.get('price') or item.get('amount') or 0
                item_id = item.get('id') or item.get('order_id') or '—'
                lines.append(f'• <b>#{item_id}</b> · {title} · {money(price)} · <i>{status}</i>')
            text = '
'.join(lines)
    except Exception:
        text = '⚠️ Не удалось загрузить историю заказов.'
    await safe_edit_or_send(callback, text, reply_markup=back_home())
    await callback.answer()


@router.callback_query(F.data == 'menu:shop')
async def menu_shop(callback: CallbackQuery) -> None:
    try:
        packages = await site_api.packages()
        if not packages:
            text = '⚠️ Каталог пакетов пока пуст или backend ещё не отдаёт пакеты.'
            markup = back_home()
        else:
            text = '<b>🛒 Покупка Robux</b>

Выбери пакет ниже 👇'
            markup = packages_keyboard(packages)
    except Exception:
        text = '⚠️ Не удалось загрузить каталог пакетов.'
        markup = back_home()
    await safe_edit_or_send(callback, text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data == 'menu:link')
async def menu_link(callback: CallbackQuery, state: FSMContext) -> None:
    if site_api.identity_params(callback.from_user.id).get('site_user_id') is not None:
        text = (
            '<b>🔗 Привязка аккаунта</b>

'
            '✅ Тестовая привязка активна.
'
            f'Все запросы сейчас идут от ID сайта: <code>{site_api.identity_params(callback.from_user.id).get("site_user_id")}</code>'
        )
    else:
        from app.handlers.link import LinkState
        await state.set_state(LinkState.waiting_code)
        text = (
            '<b>🔗 Привязка аккаунта</b>

'
            'Отправь код привязки следующим сообщением в чат.
'
            'Пример: <code>RBX-483912</code>'
        )
    await safe_edit_or_send(callback, text, reply_markup=back_home())
    await callback.answer()


@router.callback_query(F.data == 'menu:support')
async def menu_support(callback: CallbackQuery) -> None:
    text = (
        '<b>❓ Поддержка</b>

'
        'Если оплата зависла, Robux не пришли или нужно вручную проверить заказ — напиши администратору магазина.

'
        'Совет: в сообщении сразу укажи номер заказа и свой nickname.'
    )
    await safe_edit_or_send(callback, text, reply_markup=back_home())
    await callback.answer()
