"""Inline keyboards for the Robux-bot."""
from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import ROBUX_PRESETS, SITE_URL


# ── Visual constants ─────────────────────────────────────────────
EMO_ROBUX = "💎"
EMO_PROFILE = "👤"
EMO_BALANCE = "💰"
EMO_ORDERS = "📋"
EMO_TOPUP = "💳"
EMO_HELP = "❓"
EMO_SITE = "🌐"
EMO_ADMIN = "⚙️"
EMO_BACK = "←"
EMO_REFRESH = "↻"
EMO_CHECK = "✓"
EMO_CROSS = "✕"


def main_menu_kb(is_admin: bool = False, balance: int | None = None) -> InlineKeyboardMarkup:
    """Главное меню — Robux-фокус."""
    rows = [
        # Primary action — buying Robux
        [InlineKeyboardButton(text=f"{EMO_ROBUX}  Купить Robux", callback_data="robux:start")],
        # Money & profile
        [
            InlineKeyboardButton(text=f"{EMO_BALANCE} Баланс", callback_data="profile:balance"),
            InlineKeyboardButton(text=f"{EMO_TOPUP} Пополнить", url=f"{SITE_URL}/v2#topup"),
        ],
        [
            InlineKeyboardButton(text=f"{EMO_PROFILE} Профиль", callback_data="profile:show"),
            InlineKeyboardButton(text=f"{EMO_ORDERS} Заказы", callback_data="orders:list"),
        ],
        [
            InlineKeyboardButton(text=f"{EMO_HELP} Помощь", callback_data="help:show"),
            InlineKeyboardButton(text=f"{EMO_SITE} На сайт", url=SITE_URL),
        ],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text=f"{EMO_ADMIN} Админ-панель", callback_data="admin:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def link_prompt_kb() -> InlineKeyboardMarkup:
    """Шаги привязки для незалинкованных юзеров."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{EMO_SITE} Получить код на сайте", url=f"{SITE_URL}/v2")],
            [InlineKeyboardButton(text=f"{EMO_HELP} Как привязать?", callback_data="link:help")],
        ]
    )


def back_to_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{EMO_BACK} В главное меню", callback_data="menu:main")]
        ]
    )


def robux_amount_kb() -> InlineKeyboardMarkup:
    """Пресеты + кастомная сумма + сайт + назад."""
    rows = []
    line = []
    for amount in ROBUX_PRESETS:
        line.append(InlineKeyboardButton(text=f"{amount}", callback_data=f"robux:amt:{amount}"))
        if len(line) == 3:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    rows.append([
        InlineKeyboardButton(text="✏️  Своя сумма", callback_data="robux:custom"),
        InlineKeyboardButton(text=f"{EMO_REFRESH} Обновить", callback_data="robux:refresh"),
    ])
    rows.append([
        InlineKeyboardButton(text=f"{EMO_SITE}  Оформить на сайте", url=f"{SITE_URL}/v2"),
    ])
    rows.append([
        InlineKeyboardButton(text=f"{EMO_BACK} В меню", callback_data="menu:main"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def robux_confirm_kb(amount: int, can_pay: bool) -> InlineKeyboardMarkup:
    rows = []
    if can_pay:
        rows.append([
            InlineKeyboardButton(
                text=f"{EMO_SITE}  Оформить {amount} R$ на сайте",
                url=f"{SITE_URL}/v2",
            )
        ])
    else:
        rows.append([
            InlineKeyboardButton(text=f"{EMO_TOPUP}  Пополнить баланс", url=f"{SITE_URL}/v2#topup"),
        ])
    rows.append([
        InlineKeyboardButton(text=f"{EMO_BACK} Другая сумма", callback_data="robux:start"),
        InlineKeyboardButton(text=f"{EMO_REFRESH} Пересчитать", callback_data=f"robux:amt:{amount}"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_kb(is_linked: bool) -> InlineKeyboardMarkup:
    if is_linked:
        rows = [
            [
                InlineKeyboardButton(text=f"{EMO_REFRESH} Обновить", callback_data="profile:show"),
                InlineKeyboardButton(text=f"{EMO_TOPUP} Пополнить", url=f"{SITE_URL}/v2#topup"),
            ],
            [
                InlineKeyboardButton(text=f"{EMO_ORDERS} Мои заказы", callback_data="orders:list"),
                InlineKeyboardButton(text=f"{EMO_SITE} Сайт", url=SITE_URL),
            ],
            [InlineKeyboardButton(text="🔓 Отвязать аккаунт", callback_data="profile:unlink")],
            [InlineKeyboardButton(text=f"{EMO_BACK} В меню", callback_data="menu:main")],
        ]
    else:
        rows = [
            [InlineKeyboardButton(text="🔗 Привязать аккаунт", callback_data="link:start")],
            [InlineKeyboardButton(text=f"{EMO_SITE} Сайт", url=SITE_URL)],
        ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_unlink_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{EMO_CHECK} Да, отвязать", callback_data="profile:unlink:yes"),
                InlineKeyboardButton(text=f"{EMO_CROSS} Отмена", callback_data="profile:show"),
            ]
        ]
    )


def orders_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{EMO_REFRESH} Обновить", callback_data="orders:list"),
                InlineKeyboardButton(text=f"{EMO_SITE} На сайте", url=f"{SITE_URL}/v2"),
            ],
            [InlineKeyboardButton(text=f"{EMO_BACK} В меню", callback_data="menu:main")],
        ]
    )


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Свежие заказы", callback_data="admin:orders"),
                InlineKeyboardButton(text="🔍 Найти юзера", callback_data="admin:find_user"),
            ],
            [
                InlineKeyboardButton(text=f"{EMO_ROBUX} Robux настройки", callback_data="admin:robux_settings"),
                InlineKeyboardButton(text=f"{EMO_SITE} Сайт", url=f"{SITE_URL}/v2"),
            ],
            [InlineKeyboardButton(text=f"{EMO_BACK} В меню", callback_data="menu:main")],
        ]
    )
