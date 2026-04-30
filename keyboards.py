"""Inline keyboards used by the bot."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from config import ROBUX_PRESETS, SITE_URL


def main_menu_kb(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню (показывается при /start если юзер привязан)."""
    rows = [
        [
            InlineKeyboardButton(text="💎 Купить Robux", callback_data="robux:start"),
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile:show"),
        ],
        [
            InlineKeyboardButton(text="🛒 Каталог", callback_data="shop:list"),
            InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders:list"),
        ],
        [
            InlineKeyboardButton(text="💰 Баланс", callback_data="profile:balance"),
            InlineKeyboardButton(text="❓ Помощь", callback_data="help:show"),
        ],
        [InlineKeyboardButton(text="🌐 Открыть сайт", url=SITE_URL)],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def link_prompt_kb() -> InlineKeyboardMarkup:
    """Шаги привязки для незалинкованных юзеров."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Получить код на сайте", url=f"{SITE_URL}/v2")],
            [InlineKeyboardButton(text="❓ Как привязать?", callback_data="link:help")],
        ]
    )


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="‹ В главное меню", callback_data="menu:main")]
        ]
    )


def robux_amount_kb() -> InlineKeyboardMarkup:
    """6 пресетов + кастомная сумма + назад."""
    rows = []
    line = []
    for amount in ROBUX_PRESETS:
        line.append(InlineKeyboardButton(text=f"{amount} R$", callback_data=f"robux:amt:{amount}"))
        if len(line) == 3:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    rows.append([
        InlineKeyboardButton(text="✏️ Своя сумма", callback_data="robux:custom"),
    ])
    rows.append([
        InlineKeyboardButton(text="🌐 Оформить на сайте", url=f"{SITE_URL}/v2"),
        InlineKeyboardButton(text="‹ Назад", callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def robux_confirm_kb(amount: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"🌐 Оформить {amount} R$ на сайте",
                    url=f"{SITE_URL}/v2",
                )
            ],
            [InlineKeyboardButton(text="‹ Выбрать другую сумму", callback_data="robux:start")],
        ]
    )


def profile_kb(is_linked: bool) -> InlineKeyboardMarkup:
    if is_linked:
        rows = [
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="profile:show")],
            [
                InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders:list"),
                InlineKeyboardButton(text="🌐 Сайт", url=SITE_URL),
            ],
            [InlineKeyboardButton(text="🔓 Отвязать аккаунт", callback_data="profile:unlink")],
            [InlineKeyboardButton(text="‹ В меню", callback_data="menu:main")],
        ]
    else:
        rows = [
            [InlineKeyboardButton(text="🔗 Привязать аккаунт", callback_data="link:start")],
            [InlineKeyboardButton(text="🌐 Сайт", url=SITE_URL)],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_unlink_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, отвязать", callback_data="profile:unlink:yes"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="profile:show"),
            ]
        ]
    )


def orders_tabs_kb(active: str = "robux") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=("• 💎 Robux" if active == "robux" else "💎 Robux"),
                    callback_data="orders:tab:robux",
                ),
                InlineKeyboardButton(
                    text=("• 🛒 Магазин" if active == "shop" else "🛒 Магазин"),
                    callback_data="orders:tab:shop",
                ),
            ],
            [InlineKeyboardButton(text="‹ В меню", callback_data="menu:main")],
        ]
    )


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Последние заказы", callback_data="admin:orders"),
                InlineKeyboardButton(text="👤 Найти юзера", callback_data="admin:find_user"),
            ],
            [
                InlineKeyboardButton(text="💎 Robux настройки", callback_data="admin:robux_settings"),
                InlineKeyboardButton(text="🌐 Открыть сайт", url=f"{SITE_URL}/v2"),
            ],
            [InlineKeyboardButton(text="‹ В меню", callback_data="menu:main")],
        ]
    )
