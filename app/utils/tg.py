from __future__ import annotations

from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message


async def safe_edit_or_send(
    target: CallbackQuery | Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    message = target.message if isinstance(target, CallbackQuery) else target
    if message is None:
        return
    try:
        await message.edit_text(text, reply_markup=reply_markup)
        return
    except Exception:
        pass
    try:
        await message.answer(text, reply_markup=reply_markup)
    except Exception:
        pass
