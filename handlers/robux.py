"""Robux purchase flow: stock, quote, presets, custom amount."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from api import ApiError, api
from config import SITE_URL
from keyboards import back_to_menu_kb, link_prompt_kb, robux_amount_kb, robux_confirm_kb
from utils import esc, fmt_num, fmt_robux, fmt_rub

router = Router(name="robux")
log = logging.getLogger(__name__)


class RobuxStates(StatesGroup):
    waiting_for_amount = State()


async def _ensure_linked(target: Message | CallbackQuery) -> bool:
    tg_id = target.from_user.id
    try:
        link = await api.get_link(tg_id)
    except ApiError:
        link = None
    if not link:
        msg = target if isinstance(target, Message) else target.message
        await msg.answer(
            "🔗 Чтобы покупать Robux через бота, сначала привяжи аккаунт сайта.\n\n"
            "Получи код на сайте → Безопасность → Telegram-бот, затем пришли /link &lt;код&gt;.",
            reply_markup=link_prompt_kb(), parse_mode="HTML",
        )
        if isinstance(target, CallbackQuery):
            await target.answer()
        return False
    return True


async def _render_start(target: Message | CallbackQuery) -> None:
    msg = target if isinstance(target, Message) else target.message
    try:
        stock = await api.robux_stock()
    except ApiError as e:
        log.warning("robux_stock failed: %s", e)
        stock = {}

    avail = int(stock.get("available") or stock.get("stock") or 0)
    rate = stock.get("rate")
    rate_str = ""
    if rate:
        try:
            rate_str = f"~{float(rate):.2f} ₽ за 1 R$"
        except (TypeError, ValueError):
            rate_str = ""

    text = (
        "💎 <b>Покупка Robux</b>\n\n"
        f"📊 <b>В наличии:</b> {fmt_num(avail)} R$\n"
    )
    if rate_str:
        text += f"💱 <b>Курс:</b> {rate_str}\n"
    text += (
        "\nВыбери сумму ниже или введи свою.\n"
        "Минимум — <b>50 R$</b>.\n\n"
        "ℹ️ Доставка идёт через геймпасс (~5-15 минут). "
        "Финальное оформление — на сайте, чтобы можно было ввести ссылку на геймпасс или ник."
    )
    if isinstance(target, CallbackQuery):
        try:
            await msg.edit_text(text, reply_markup=robux_amount_kb(), parse_mode="HTML")
        except Exception:
            await msg.answer(text, reply_markup=robux_amount_kb(), parse_mode="HTML")
        await target.answer()
    else:
        await msg.answer(text, reply_markup=robux_amount_kb(), parse_mode="HTML")


@router.message(Command("buy"))
@router.message(Command("robux"))
async def cmd_buy(msg: Message, state: FSMContext):
    if not await _ensure_linked(msg):
        return
    await state.clear()
    await _render_start(msg)


@router.callback_query(F.data == "robux:start")
async def cb_robux_start(cb: CallbackQuery, state: FSMContext):
    if not await _ensure_linked(cb):
        return
    await state.clear()
    await _render_start(cb)


async def _show_quote(target: Message | CallbackQuery, amount: int) -> None:
    msg = target if isinstance(target, Message) else target.message
    if amount < 50:
        text = "❌ Минимальная сумма — <b>50 R$</b>. Выбери побольше."
        await msg.answer(text, reply_markup=robux_amount_kb(), parse_mode="HTML")
        if isinstance(target, CallbackQuery):
            await target.answer()
        return

    try:
        balance = await api.get_balance(target.from_user.id)
    except ApiError:
        balance = 0

    try:
        quote = await api.robux_quote(amount)
    except ApiError as e:
        await msg.answer(f"⚠️ Не удалось рассчитать цену: <i>{esc(e)}</i>", parse_mode="HTML")
        if isinstance(target, CallbackQuery):
            await target.answer()
        return

    rub_price = int(quote.get("rub_price") or quote.get("price") or 0)
    gp_amount = quote.get("gamepass_robux") or quote.get("gamepass_price") or amount
    rate = quote.get("rate")
    can_pay = balance >= rub_price

    lines = [
        f"💎 <b>{fmt_robux(amount)}</b>",
        "",
        f"💰 <b>К оплате:</b> {fmt_rub(rub_price)}",
    ]
    if rate:
        try:
            lines.append(f"💱 <b>Курс:</b> {float(rate):.2f} ₽/R$")
        except (TypeError, ValueError):
            pass
    if gp_amount and int(gp_amount) != amount:
        lines.append(f"🎫 <b>Геймпасс:</b> {fmt_num(gp_amount)} R$ (с учётом комиссии Roblox)")
    lines.append("")
    lines.append(f"<b>Твой баланс:</b> {fmt_rub(balance)}")

    if can_pay:
        lines.append("\n✅ Баланса достаточно. Оформи заказ на сайте — там укажешь ник/геймпасс.")
    else:
        diff = rub_price - balance
        lines.append(f"\n⚠️ Не хватает <b>{fmt_rub(diff)}</b>. Сначала пополни баланс на сайте.")

    text = "\n".join(lines)
    if isinstance(target, CallbackQuery):
        try:
            await msg.edit_text(text, reply_markup=robux_confirm_kb(amount), parse_mode="HTML")
        except Exception:
            await msg.answer(text, reply_markup=robux_confirm_kb(amount), parse_mode="HTML")
        await target.answer()
    else:
        await msg.answer(text, reply_markup=robux_confirm_kb(amount), parse_mode="HTML")


@router.callback_query(F.data.startswith("robux:amt:"))
async def cb_robux_amount(cb: CallbackQuery, state: FSMContext):
    if not await _ensure_linked(cb):
        return
    await state.clear()
    try:
        amount = int(cb.data.split(":")[2])
    except (ValueError, IndexError):
        await cb.answer("Неверная сумма", show_alert=True)
        return
    await _show_quote(cb, amount)


@router.callback_query(F.data == "robux:custom")
async def cb_robux_custom(cb: CallbackQuery, state: FSMContext):
    if not await _ensure_linked(cb):
        return
    await state.set_state(RobuxStates.waiting_for_amount)
    text = (
        "✏️ <b>Введи количество Robux</b>\n\n"
        "Просто отправь число — например, <code>2500</code>.\n"
        "Минимум — <b>50 R$</b>, максимум — <b>50 000 R$</b>.\n\n"
        "Чтобы отменить — нажми /menu."
    )
    try:
        await cb.message.edit_text(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
    except Exception:
        await cb.message.answer(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
    await cb.answer()


@router.message(RobuxStates.waiting_for_amount)
async def msg_custom_amount(msg: Message, state: FSMContext):
    raw = (msg.text or "").strip().replace(" ", "").replace(",", "")
    if not raw.isdigit():
        await msg.answer(
            "❌ Это не число. Введи количество Robux цифрами, например <code>2500</code>.",
            parse_mode="HTML",
        )
        return
    amount = int(raw)
    if amount < 50:
        await msg.answer("❌ Минимум — <b>50 R$</b>. Введи побольше.", parse_mode="HTML")
        return
    if amount > 50000:
        await msg.answer(
            "❌ Максимум через бота — <b>50 000 R$</b>.\n"
            f"Для большего объёма оформи заказ на сайте: {SITE_URL}/v2",
            parse_mode="HTML",
        )
        return
    await state.clear()
    await _show_quote(msg, amount)
