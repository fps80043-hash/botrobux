"""Profile, balance & unlink-confirm flow."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from api import ApiError, api
from keyboards import confirm_unlink_kb, link_prompt_kb, profile_kb
from utils import esc, fmt_rub, is_premium_active, parse_iso

router = Router(name="profile")
log = logging.getLogger(__name__)


def _profile_text(profile: dict, link: dict | None) -> str:
    username = profile.get("username") or "—"
    balance = int(profile.get("balance") or 0)
    email = profile.get("email") or ""
    is_admin = bool(profile.get("is_admin"))
    prem = is_premium_active(profile.get("premium_until"))

    lines = [
        f"👤 <b>{esc(username)}</b>",
    ]
    badges = []
    if is_admin:
        badges.append("🛡 ADMIN")
    if prem:
        badges.append("⭐ PREMIUM")
    if badges:
        lines.append("   " + "  ".join(badges))
    lines.append("")
    lines.append(f"<b>Баланс:</b>  {fmt_rub(balance)}")
    lines.append(f"<b>ID:</b>  <code>#{int(profile.get('id') or 0)}</code>")
    if email:
        lines.append(f"<b>Email:</b>  <code>{esc(email)}</code>")
    if prem:
        until = parse_iso(profile.get("premium_until"))
        if until:
            lines.append(f"<b>Premium до:</b>  {until.strftime('%d.%m.%Y')}")
    if link:
        tg_un = link.get("telegram_username")
        if tg_un:
            lines.append(f"<b>Telegram:</b>  @{esc(tg_un)}")
    return "\n".join(lines)


async def _show_profile(target: Message | CallbackQuery) -> None:
    msg = target if isinstance(target, Message) else target.message
    tg_id = target.from_user.id

    try:
        link = await api.get_link(tg_id)
    except ApiError as e:
        await msg.answer(f"⚠️ Ошибка: <i>{esc(e)}</i>", parse_mode="HTML")
        return

    if not link:
        text = (
            "👤 <b>Профиль</b>\n\n"
            "У тебя ещё нет привязанного аккаунта сайта.\n"
            "Нажми «Привязать аккаунт», чтобы видеть здесь баланс, "
            "заказы и историю покупок."
        )
        if isinstance(target, CallbackQuery):
            try:
                await msg.edit_text(text, reply_markup=profile_kb(False), parse_mode="HTML")
            except Exception:
                await msg.answer(text, reply_markup=profile_kb(False), parse_mode="HTML")
        else:
            await msg.answer(text, reply_markup=profile_kb(False), parse_mode="HTML")
        return

    try:
        profile = await api.get_profile(tg_id)
    except ApiError as e:
        await msg.answer(f"⚠️ Не удалось загрузить профиль: <i>{esc(e)}</i>", parse_mode="HTML")
        return

    text = _profile_text(profile, link)
    if isinstance(target, CallbackQuery):
        try:
            await msg.edit_text(text, reply_markup=profile_kb(True), parse_mode="HTML")
        except Exception:
            await msg.answer(text, reply_markup=profile_kb(True), parse_mode="HTML")
    else:
        await msg.answer(text, reply_markup=profile_kb(True), parse_mode="HTML")


@router.message(Command("profile"))
async def cmd_profile(msg: Message):
    await _show_profile(msg)


@router.message(Command("balance"))
async def cmd_balance(msg: Message):
    tg_id = msg.from_user.id
    try:
        link = await api.get_link(tg_id)
    except ApiError as e:
        await msg.answer(f"⚠️ Ошибка: {esc(e)}", parse_mode="HTML")
        return
    if not link:
        await msg.answer(
            "Сначала привяжи аккаунт сайта: /link &lt;код&gt;",
            parse_mode="HTML", reply_markup=link_prompt_kb(),
        )
        return
    try:
        balance = await api.get_balance(tg_id)
    except ApiError as e:
        await msg.answer(f"⚠️ Ошибка: {esc(e)}", parse_mode="HTML")
        return
    await msg.answer(f"💰 <b>Баланс:</b> {fmt_rub(balance)}", parse_mode="HTML")


@router.callback_query(F.data == "profile:show")
async def cb_profile(cb: CallbackQuery):
    await _show_profile(cb)
    await cb.answer()


@router.callback_query(F.data == "profile:balance")
async def cb_balance(cb: CallbackQuery):
    tg_id = cb.from_user.id
    try:
        balance = await api.get_balance(tg_id)
    except ApiError as e:
        await cb.answer(f"Ошибка: {e}", show_alert=True)
        return
    await cb.answer(f"💰 Баланс: {fmt_rub(balance)}", show_alert=True)


@router.callback_query(F.data == "profile:unlink")
async def cb_unlink_ask(cb: CallbackQuery):
    text = (
        "🔓 <b>Отвязать аккаунт?</b>\n\n"
        "После отвязки бот перестанет показывать твой баланс и заказы.\n"
        "Данные на сайте сохранятся — это просто разрыв связи Telegram ↔ сайт.\n\n"
        "Чтобы привязать снова — получи новый код на сайте."
    )
    try:
        await cb.message.edit_text(text, reply_markup=confirm_unlink_kb(), parse_mode="HTML")
    except Exception:
        await cb.message.answer(text, reply_markup=confirm_unlink_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "profile:unlink:yes")
async def cb_unlink_yes(cb: CallbackQuery):
    tg_id = cb.from_user.id
    try:
        await api.unlink(tg_id)
    except ApiError as e:
        await cb.answer(f"Ошибка: {e}", show_alert=True)
        return
    await cb.message.edit_text(
        "✅ Аккаунт отвязан.\n\nЕсли захочешь привязать снова — пришли /link с новым кодом.",
        reply_markup=link_prompt_kb(), parse_mode="HTML",
    )
    await cb.answer("Отвязано")
