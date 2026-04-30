"""/start, /help, /menu and main-menu inline routing."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from api import ApiError, api
from config import ADMIN_TG_IDS, BOT_NAME
from keyboards import link_prompt_kb, main_menu_kb
from utils import esc

router = Router(name="start")
log = logging.getLogger(__name__)


WELCOME_LINKED = (
    "👋 <b>Привет, {username}!</b>\n\n"
    "Это <b>{bot}</b> — здесь ты можешь:\n\n"
    "💎 Покупать Robux по нику или ссылке\n"
    "🛒 Смотреть каталог магазина\n"
    "👤 Управлять профилем и балансом\n"
    "📦 Отслеживать свои заказы\n\n"
    "<b>Баланс:</b> {balance}"
)

WELCOME_NEW = (
    "👋 <b>Добро пожаловать в {bot}!</b>\n\n"
    "Чтобы начать пользоваться, нужно <b>привязать аккаунт сайта</b>:\n\n"
    "<b>1.</b> Открой сайт и зайди в свой профиль\n"
    "<b>2.</b> В разделе «Безопасность» нажми «Получить код привязки»\n"
    "<b>3.</b> Отправь мне сюда:  <code>/link &lt;код&gt;</code>\n\n"
    "Если у тебя ещё нет аккаунта — зарегистрируйся на сайте."
)

HELP_TEXT = (
    "❓ <b>Команды бота</b>\n\n"
    "/start — главное меню\n"
    "/menu — главное меню\n"
    "/profile — твой профиль и баланс\n"
    "/balance — быстрая проверка баланса\n"
    "/buy — покупка Robux\n"
    "/orders — твои заказы\n"
    "/shop — каталог магазина\n"
    "/link &lt;код&gt; — привязать аккаунт сайта\n"
    "/unlink — отвязать аккаунт\n"
    "/help — это сообщение\n\n"
    "Все вопросы и проблемы — пиши в поддержку на сайте."
)


def _fmt_balance(amount: int) -> str:
    s = f"{int(amount):,}".replace(",", " ")
    return f"<b>{s} ₽</b>"


@router.message(CommandStart(deep_link=True))
async def start_with_deeplink(msg: Message, command):
    """Handle /start <payload> — used for deep-link account binding via ?start=link_<code>."""
    payload = (command.args or "").strip() if command and command.args else ""
    if payload.startswith("link_"):
        code = payload[5:].strip()
        if code:
            from .link import perform_link
            await perform_link(msg, code)
            return
    # Fallback to normal start
    await cmd_start(msg)


@router.message(CommandStart())
@router.message(Command("menu"))
async def cmd_start(msg: Message):
    tg_id = msg.from_user.id
    try:
        link = await api.get_link(tg_id)
    except ApiError as e:
        log.warning("get_link failed: %s", e)
        link = None

    if not link:
        await msg.answer(
            WELCOME_NEW.format(bot=BOT_NAME),
            reply_markup=link_prompt_kb(),
            parse_mode="HTML",
        )
        return

    try:
        profile = await api.get_profile(tg_id)
    except ApiError as e:
        await msg.answer(
            f"⚠️ Не удалось загрузить твой профиль: <i>{esc(e)}</i>\n"
            f"Попробуй ещё раз через минуту или открой сайт.",
            parse_mode="HTML",
        )
        return

    is_admin = bool(profile.get("is_admin")) or tg_id in ADMIN_TG_IDS
    text = WELCOME_LINKED.format(
        username=esc(profile.get("username") or "друг"),
        bot=BOT_NAME,
        balance=_fmt_balance(profile.get("balance") or 0),
    )
    await msg.answer(text, reply_markup=main_menu_kb(is_admin=is_admin), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(HELP_TEXT, parse_mode="HTML")


@router.callback_query(F.data == "menu:main")
async def cb_main_menu(cb: CallbackQuery):
    """Re-render main menu in place."""
    tg_id = cb.from_user.id
    try:
        link = await api.get_link(tg_id)
    except ApiError:
        link = None

    if not link:
        await cb.message.edit_text(
            WELCOME_NEW.format(bot=BOT_NAME),
            reply_markup=link_prompt_kb(),
            parse_mode="HTML",
        )
        await cb.answer()
        return

    try:
        profile = await api.get_profile(tg_id)
    except ApiError as e:
        await cb.answer(f"Ошибка: {e}", show_alert=True)
        return

    is_admin = bool(profile.get("is_admin")) or tg_id in ADMIN_TG_IDS
    text = WELCOME_LINKED.format(
        username=esc(profile.get("username") or "друг"),
        bot=BOT_NAME,
        balance=_fmt_balance(profile.get("balance") or 0),
    )
    try:
        await cb.message.edit_text(text, reply_markup=main_menu_kb(is_admin=is_admin), parse_mode="HTML")
    except Exception:
        await cb.message.answer(text, reply_markup=main_menu_kb(is_admin=is_admin), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "help:show")
async def cb_help(cb: CallbackQuery):
    await cb.message.answer(HELP_TEXT, parse_mode="HTML")
    await cb.answer()
