from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def terms_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Принимаю', callback_data='terms:accept')],
        ]
    )


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text='🛒 Купить Robux', callback_data='menu:shop'),
            InlineKeyboardButton(text='👤 Профиль', callback_data='menu:profile'),
        ],
        [
            InlineKeyboardButton(text='💳 Баланс', callback_data='menu:balance'),
            InlineKeyboardButton(text='📦 Наличие', callback_data='menu:stock'),
        ],
        [
            InlineKeyboardButton(text='📜 Мои заказы', callback_data='menu:orders'),
            InlineKeyboardButton(text='🔗 Привязка', callback_data='menu:link'),
        ],
        [
            InlineKeyboardButton(text='❓ Поддержка', callback_data='menu:support'),
            InlineKeyboardButton(text='🔄 Обновить', callback_data='menu:home'),
        ],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text='🛠 Админка', callback_data='admin:home')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_home() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='🏠 В главное меню', callback_data='menu:home')]]
    )


def packages_keyboard(packages: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for item in packages[:12]:
        title = item.get('title') or f"{item.get('robux_amount', 0)} Robux"
        price = item.get('price', 0)
        rows.append([InlineKeyboardButton(text=f'✨ {title} — {price} ₽', callback_data=f"buy:pick:{item.get('id')}")])
    rows.append([InlineKeyboardButton(text='🔙 Назад', callback_data='menu:home')])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_purchase_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✅ Подтвердить покупку', callback_data='buy:confirm')],
            [InlineKeyboardButton(text='❌ Отмена', callback_data='menu:shop')],
        ]
    )


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='💸 Цены', callback_data='admin:prices'),
                InlineKeyboardButton(text='📦 Остаток', callback_data='admin:stock'),
            ],
            [
                InlineKeyboardButton(text='📜 Заказы', callback_data='admin:orders'),
                InlineKeyboardButton(text='👤 Пользователь', callback_data='admin:user'),
            ],
            [
                InlineKeyboardButton(text='🖼 Стартовая GIF', callback_data='admin:gif'),
                InlineKeyboardButton(text='🏠 Меню', callback_data='menu:home'),
            ],
        ]
    )


def admin_prices_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✏️ Изменить цену за 1 Robux', callback_data='admin:set_price')],
            [InlineKeyboardButton(text='🔙 Назад в админку', callback_data='admin:home')],
        ]
    )


def admin_stock_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='➕ Изменить остаток Robux', callback_data='admin:set_stock')],
            [InlineKeyboardButton(text='🔙 Назад в админку', callback_data='admin:home')],
        ]
    )


def admin_gif_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✏️ Задать GIF/animation file_id', callback_data='admin:set_gif')],
            [InlineKeyboardButton(text='🔙 Назад в админку', callback_data='admin:home')],
        ]
    )


def admin_user_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='💰 Изменить баланс', callback_data='admin:set_balance')],
            [InlineKeyboardButton(text='🔙 Назад в админку', callback_data='admin:home')],
        ]
    )
