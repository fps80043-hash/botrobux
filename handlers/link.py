"""Account linking flow: /link <code>, /unlink, and the 'How to link?' button."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from api import ApiError, api
from config import BOT_NAME, SITE_URL
from keyboards import back_to_menu_kb, link_prompt_kb, main_menu_kb
from utils import esc, fmt_rub

router = Router(name="link")
log = logging.getLogger(__name__)


HOW_TO_LINK = (
    "🔗 <b>Как привязать аккаунт</b>\n\n"
    "Привязка нужна чтобы бот знал кто ты на сайте — иначе мы не сможем "
    "показать твой баланс, заказы и историю.\n\n"
    "<b>Шаги:</b>\n\n"
    "1️⃣  Открой <a href='{site}'>сайт</a> и войди в свой аккаунт\n"
    "2️⃣  Нажми на свой профиль → <b>Безопасность</b>\n"
    "3️⃣  В блоке <b>Telegram-бот</b> нажми «Получить код»\n"
    "4️⃣  Скопируй 6-значный код и пришли мне:\n"
    "        <code>/link 123456</code>\n\n"
    "Код действует <b>10 минут</b>. Если не успел — сгенерируй новый.\n\n"
    "Если у тебя ещё нет аккаунта — зарегистрируйся на сайте."
).format(site=SITE_URL)


async def perform_link(msg: Message, code: str) -> None:
    """Common entry-point used by both /link command and deep-link /start link_<code>."""
    code = (code or "").strip().replace(" ", "").replace("-", "")
    if not code or not code.isdigit() or len(code) != 6:
        await msg.answer(
            "❌ Код должен состоять из 6 цифр.\n\n"
            "Получи свежий код на сайте → Профиль → Безопасность → Telegram-бот.",
            parse_mode="HTML",
        )
        return

    tg_id = msg.from_user.id
    tg_username = msg.from_user.username or ""

    # Check existing link first to give a clearer message
    try:
        existing = await api.get_link(tg_id)
    except ApiError:
        existing = None
    if existing:
        await msg.answer(
            "⚠️ Этот Telegram уже привязан к аккаунту.\n"
            "Чтобы перепривязать к другому — сначала отправь /unlink.",
            parse_mode="HTML",
        )
        return

    try:
        result = await api.link_by_code(code, tg_id, tg_username)
    except ApiError as e:
        if e.status == 400:
            await msg.answer(
                "❌ <b>Код не принят</b>\n\n"
                "Возможные причины:\n"
                "• Код уже использован или истёк (10 мин)\n"
                "• Опечатка в цифрах\n\n"
                "Сгенерируй новый код на сайте: Профиль → Безопасность → Telegram-бот.",
                parse_mode="HTML",
            )
        else:
            await msg.answer(f"⚠️ Ошибка при привязке: <i>{esc(e)}</i>", parse_mode="HTML")
        return

    username = result.get("username") or "друг"
    balance = int(result.get("balance") or 0)
    success_text = (
        f"✅ <b>Аккаунт привязан!</b>\n\n"
        f"Привет, <b>{esc(username)}</b> 👋\n"
        f"Твой баланс: <b>{fmt_rub(balance)}</b>\n\n"
        f"Теперь можешь пользоваться всеми функциями бота. Нажми /menu чтобы открыть меню."
    )
    await msg.answer(success_text, reply_markup=main_menu_kb(), parse_mode="HTML")


@router.message(Command("link"))
async def cmd_link(msg: Message, command):
    code = (command.args or "").strip()
    if not code:
        await msg.answer(
            "Используй: <code>/link 123456</code>\n\n"
            "Где взять код — нажми «Как привязать?» в /menu.",
            parse_mode="HTML",
            reply_markup=link_prompt_kb(),
        )
        return
    await perform_link(msg, code)


@router.message(Command("unlink"))
async def cmd_unlink(msg: Message):
    tg_id = msg.from_user.id
    try:
        link = await api.get_link(tg_id)
    except ApiError as e:
        await msg.answer(f"Ошибка: {esc(e)}", parse_mode="HTML")
        return
    if not link:
        await msg.answer("ℹ️ Этот Telegram не привязан ни к одному аккаунту.", parse_mode="HTML")
        return
    try:
        await api.unlink(tg_id)
    except ApiError as e:
        await msg.answer(f"⚠️ Ошибка: <i>{esc(e)}</i>", parse_mode="HTML")
        return
    await msg.answer(
        "✅ Аккаунт отвязан. Чтобы привязать другой — пришли /link с новым кодом.",
        reply_markup=link_prompt_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "link:help")
async def cb_link_help(cb: CallbackQuery):
    try:
        await cb.message.edit_text(
            HOW_TO_LINK, reply_markup=back_to_menu_kb(),
            parse_mode="HTML", disable_web_page_preview=True,
        )
    except Exception:
        await cb.message.answer(
            HOW_TO_LINK, reply_markup=back_to_menu_kb(),
            parse_mode="HTML", disable_web_page_preview=True,
        )
    await cb.answer()


@router.callback_query(F.data == "link:start")
async def cb_link_start(cb: CallbackQuery):
    await cb_link_help(cb)
