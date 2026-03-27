from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Купить Robux"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="📦 Наличие"), KeyboardButton(text="📜 Мои заказы")],
            [KeyboardButton(text="🔗 Привязать аккаунт")],
        ],
        resize_keyboard=True,
    )


def packages_keyboard(packages: list[dict]) -> InlineKeyboardMarkup:
    rows = []
    for item in packages:
        title = item.get("title", f'{item.get("robux_amount", 0)} Robux')
        price = item.get("price", 0)
        button = InlineKeyboardButton(
            text=f"{title} • {price} ₽",
            callback_data=f"buy:{item['id']}",
        )
        rows.append([button])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
