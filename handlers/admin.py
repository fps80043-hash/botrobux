"""Admin commands — restricted by both ADMIN_TG_IDS env var and is_admin from site profile."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from api import ApiError, api
from config import ADMIN_TG_IDS, SITE_URL
from keyboards import admin_menu_kb, back_to_menu_kb
from utils import esc, fmt_relative, fmt_rub, status_label

router = Router(name="admin")
log = logging.getLogger(__name__)


class AdminStates(StatesGroup):
    finding_user = State()


async def _is_admin(tg_id: int) -> bool:
    if tg_id in ADMIN_TG_IDS:
        return True
    try:
        profile = await api.get_profile(tg_id)
    except ApiError:
        return False
    return bool(profile.get("is_admin"))


async def _deny(target: Message | CallbackQuery) -> None:
    msg = target if isinstance(target, Message) else target.message
    if isinstance(target, CallbackQuery):
        await target.answer("⛔ Нет доступа", show_alert=True)
    else:
        await msg.answer("⛔ Эта команда только для администраторов.")


def _admin_intro() -> str:
    return (
        "🛠 <b>Админ-панель</b>\n\n"
        "Доступные действия:\n"
        "• <b>Последние заказы</b> — свежие Robux-заказы\n"
        "• <b>Найти юзера</b> — поиск по нику или email\n"
        "• <b>Robux настройки</b> — текущий курс и наличие\n\n"
        "Для управления магазином, банами, выплатами — открой сайт."
    )


@router.message(Command("admin"))
async def cmd_admin(msg: Message):
    if not await _is_admin(msg.from_user.id):
        await _deny(msg)
        return
    await msg.answer(_admin_intro(), reply_markup=admin_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin:menu")
async def cb_admin_menu(cb: CallbackQuery, state: FSMContext):
    if not await _is_admin(cb.from_user.id):
        await _deny(cb)
        return
    await state.clear()
    try:
        await cb.message.edit_text(_admin_intro(), reply_markup=admin_menu_kb(), parse_mode="HTML")
    except Exception:
        await cb.message.answer(_admin_intro(), reply_markup=admin_menu_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "admin:orders")
async def cb_admin_orders(cb: CallbackQuery):
    if not await _is_admin(cb.from_user.id):
        await _deny(cb)
        return
    try:
        data = await api.admin_orders_recent(cb.from_user.id, limit=15)
    except ApiError as e:
        await cb.answer(f"Ошибка: {e}", show_alert=True)
        return
    items = data.get("orders") or data.get("items") or []
    if not items:
        text = "📊 <b>Последние заказы</b>\n\n<i>Заказов пока нет.</i>"
    else:
        lines = ["📊 <b>Последние Robux-заказы</b>", ""]
        for o in items[:15]:
            oid = int(o.get("id") or 0)
            user = esc(o.get("username") or f"#{o.get('user_id') or '?'}")
            amount = int(o.get("robux_amount") or 0)
            rub = int(o.get("rub_price") or 0)
            st = status_label(str(o.get("status") or ""))
            when = fmt_relative(o.get("created_at"))
            lines.append(
                f"#{oid}  ·  <b>{user}</b>\n"
                f"   {amount:,} R$".replace(",", " ") + f"  ·  {fmt_rub(rub)}  ·  {st}\n"
                f"   <i>{esc(when)}</i>"
            )
            lines.append("")
        text = "\n".join(lines)
    try:
        await cb.message.edit_text(text, reply_markup=admin_menu_kb(), parse_mode="HTML")
    except Exception:
        await cb.message.answer(text, reply_markup=admin_menu_kb(), parse_mode="HTML")
    await cb.answer()


@router.callback_query(F.data == "admin:find_user")
async def cb_admin_find_user(cb: CallbackQuery, state: FSMContext):
    if not await _is_admin(cb.from_user.id):
        await _deny(cb)
        return
    await state.set_state(AdminStates.finding_user)
    text = (
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Отправь ник, email или ID одним сообщением.\n\n"
        "Чтобы отменить — нажми /menu или кнопку ниже."
    )
    try:
        await cb.message.edit_text(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
    except Exception:
        await cb.message.answer(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
    await cb.answer()


@router.message(AdminStates.finding_user)
async def msg_admin_find_user(msg: Message, state: FSMContext):
    if not await _is_admin(msg.from_user.id):
        await state.clear()
        await _deny(msg)
        return
    query = (msg.text or "").strip()
    if not query:
        await msg.answer("Пустой запрос, попробуй ещё раз.")
        return
    await state.clear()
    try:
        data = await api.admin_users_find(msg.from_user.id, query)
    except ApiError as e:
        await msg.answer(f"⚠️ Ошибка: <i>{esc(e)}</i>", parse_mode="HTML")
        return
    users = data.get("users") or data.get("items") or []
    if not users:
        await msg.answer(
            f"🔍 По запросу <b>{esc(query)}</b> ничего не найдено.",
            reply_markup=admin_menu_kb(), parse_mode="HTML",
        )
        return
    lines = [f"🔍 <b>Найдено: {len(users)}</b>", ""]
    for u in users[:10]:
        uid = int(u.get("id") or 0)
        username = esc(u.get("username") or "—")
        email = esc(u.get("email") or "—")
        balance = int(u.get("balance") or 0)
        is_admin = bool(u.get("is_admin"))
        badges = " 🛡" if is_admin else ""
        lines.append(
            f"<b>#{uid}</b>  ·  <b>{username}</b>{badges}\n"
            f"   {email}  ·  {fmt_rub(balance)}"
        )
    if len(users) > 10:
        lines.append("")
        lines.append(f"<i>… ещё {len(users) - 10}. Уточни запрос.</i>")
    await msg.answer("\n".join(lines), reply_markup=admin_menu_kb(), parse_mode="HTML")


@router.callback_query(F.data == "admin:robux_settings")
async def cb_admin_robux_settings(cb: CallbackQuery):
    if not await _is_admin(cb.from_user.id):
        await _deny(cb)
        return
    try:
        # Re-use public stock endpoint — admin one has more, but stock is enough for a glance
        stock = await api.robux_stock()
    except ApiError as e:
        await cb.answer(f"Ошибка: {e}", show_alert=True)
        return
    avail = int(stock.get("available") or stock.get("stock") or 0)
    rate = stock.get("rate")
    rate_str = ""
    if rate:
        try:
            rate_str = f"{float(rate):.4f} ₽/R$"
        except (TypeError, ValueError):
            rate_str = str(rate)
    text = (
        "💎 <b>Robux настройки</b>\n\n"
        f"<b>В наличии:</b> {avail:,} R$\n".replace(",", " ")
        + (f"<b>Курс:</b> {rate_str}\n" if rate_str else "")
        + f"\nДля изменения настроек — открой админ-панель на сайте: {SITE_URL}/v2"
    )
    try:
        await cb.message.edit_text(text, reply_markup=admin_menu_kb(), parse_mode="HTML")
    except Exception:
        await cb.message.answer(text, reply_markup=admin_menu_kb(), parse_mode="HTML")
    await cb.answer()
