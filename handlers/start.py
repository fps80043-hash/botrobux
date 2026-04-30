"""/start, /help, /menu and main-menu inline routing."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from api import ApiError, api
from config import ADMIN_TG_IDS, BOT_NAME, BOT_TAGLINE
from keyboards import link_prompt_kb, main_menu_kb
from utils import esc, fmt_relative, fmt_rub, is_premium_active

router = Router(name="start")
log = logging.getLogger(__name__)


WELCOME_LINKED_TEMPLATE = (
    "💎  <b>{bot}</b>\n"
    "<i>{tagline}</i>\n"
    "{rule}\n\n"
    "Привет, <b>{username}</b>! {badges}\n\n"
    "💰  Баланс:  <b>{balance}</b>\n"
    "🆔  ID:  <code>#{uid}</code>"
    "{premium_line}"
    "\n\n"
    "{rule}\n"
    "Выбери что делать ↓"
)

WELCOME_NEW = (
    "💎  <b>{bot}</b>\n"
    "<i>{tagline}</i>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "👋  Добро пожаловать!\n\n"
    "Чтобы покупать Robux через бота, нужно <b>привязать аккаунт сайта</b> — "
    "это занимает 30 секунд:\n\n"
    "<b>1.</b>  Зайди на сайт и войди в аккаунт\n"
    "<b>2.</b>  Профиль → <b>Безопасность</b> → блок Telegram-бот\n"
    "<b>3.</b>  Нажми «Получить код привязки»\n"
    "<b>4.</b>  Пришли мне:  <code>/link 123456</code>\n\n"
    "Если у тебя ещё нет аккаунта — зарегистрируйся на сайте, это бесплатно."
)

HELP_TEXT = (
    "💎  <b>Команды бота</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "<b>Покупка Robux</b>\n"
    "/buy  •  /robux — открыть калькулятор\n\n"
    "<b>Аккаунт и баланс</b>\n"
    "/profile — профиль\n"
    "/balance — текущий баланс\n"
    "/orders — мои заказы\n\n"
    "<b>Привязка</b>\n"
    "/link &lt;код&gt; — привязать аккаунт сайта\n"
    "/unlink — отвязать\n\n"
    "<b>Прочее</b>\n"
    "/menu — главное меню\n"
    "/help — это сообщение\n\n"
    "<i>По любым вопросам — поддержка на сайте.</i>"
)


def _badges(profile: dict) -> str:
    out = []
    if profile.get("is_admin"):
        out.append("🛡 ADMIN")
    if is_premium_active(profile.get("premium_until")):
        out.append("⭐ PREMIUM")
    return "  ".join(out)


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
            WELCOME_NEW.format(bot=BOT_NAME, tagline=BOT_TAGLINE),
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

    text = _format_main_menu(profile)
    is_admin = bool(profile.get("is_admin")) or tg_id in ADMIN_TG_IDS
    await msg.answer(
        text,
        reply_markup=main_menu_kb(is_admin=is_admin, balance=profile.get("balance")),
        parse_mode="HTML",
    )


def _format_main_menu(profile: dict) -> str:
    badges = _badges(profile)
    is_prem = is_premium_active(profile.get("premium_until"))
    premium_line = ""
    if is_prem:
        from utils import parse_iso
        until = parse_iso(profile.get("premium_until"))
        if until:
            premium_line = f"\n⭐  Premium до:  <b>{until.strftime('%d.%m.%Y')}</b>"
    rule = "━━━━━━━━━━━━━━━━━━━━━━"
    return WELCOME_LINKED_TEMPLATE.format(
        bot=BOT_NAME,
        tagline=BOT_TAGLINE,
        rule=rule,
        username=esc(profile.get("username") or "друг"),
        badges=badges or "",
        balance=fmt_rub(profile.get("balance") or 0),
        uid=int(profile.get("id") or 0),
        premium_line=premium_line,
    )


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
        try:
            await cb.message.edit_text(
                WELCOME_NEW.format(bot=BOT_NAME, tagline=BOT_TAGLINE),
                reply_markup=link_prompt_kb(),
                parse_mode="HTML",
            )
        except Exception:
            await cb.message.answer(
                WELCOME_NEW.format(bot=BOT_NAME, tagline=BOT_TAGLINE),
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
    text = _format_main_menu(profile)
    try:
        await cb.message.edit_text(
            text,
            reply_markup=main_menu_kb(is_admin=is_admin, balance=profile.get("balance")),
            parse_mode="HTML",
        )
    except Exception:
        await cb.message.answer(
            text,
            reply_markup=main_menu_kb(is_admin=is_admin, balance=profile.get("balance")),
            parse_mode="HTML",
        )
    await cb.answer()


@router.callback_query(F.data == "help:show")
async def cb_help(cb: CallbackQuery):
    from keyboards import back_to_menu_kb
    try:
        await cb.message.edit_text(HELP_TEXT, reply_markup=back_to_menu_kb(), parse_mode="HTML")
    except Exception:
        await cb.message.answer(HELP_TEXT, reply_markup=back_to_menu_kb(), parse_mode="HTML")
    await cb.answer()
