"""In-bot balance top-up. Creates a payment on the site (same balance as the
website — paying via the bot credits the site account automatically) and polls
until it's paid."""
from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from api import ApiError, api
from config import SITE_URL
from keyboards import back_to_menu_kb
from premoji import eid, pe
from utils import esc, fmt_rub, typing

router = Router(name="topup")
log = logging.getLogger(__name__)

RULE = "━━━━━━━━━━━━━━━━━━━━━━"
PRESETS = [100, 300, 500, 1000, 2000, 5000]
_SPIN = ["◐", "◓", "◑", "◒"]


class TopupStates(StatesGroup):
    waiting_amount = State()


def _amount_kb() -> InlineKeyboardMarkup:
    rows, line = [], []
    for a in PRESETS:
        line.append(InlineKeyboardButton(text=f"{a} ₽", callback_data=f"topup:amt:{a}"))
        if len(line) == 3:
            rows.append(line); line = []
    if line:
        rows.append(line)
    rows.append([InlineKeyboardButton(text="Своя сумма", callback_data="topup:custom",
                                      icon_custom_emoji_id=eid("pencil"))])
    rows.append([InlineKeyboardButton(text="◁  В меню", callback_data="menu:main",
                                      icon_custom_emoji_id=eid("home"))])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# method id → (button label, premoji icon)
_METHODS = {
    "crypto":   ("CryptoBot (от 10 ₽)",   "money"),
    "stars":    ("Telegram Stars ⭐",      "star"),
    "platega":  ("Карта / СБП",           "money_in"),
}


async def _show_methods(msg: Message, amount: int) -> None:
    """After the amount is chosen — let the user pick HOW to pay."""
    await typing(msg)
    try:
        cfg = await api.topup_config()
    except ApiError:
        cfg = {}
    enabled = [m for m in ("crypto", "stars", "platega") if (cfg.get(m) or {}).get("enabled")]
    if not enabled:
        await msg.answer(
            f"{pe('cross')}  <b>Оплата временно недоступна</b>\n\n"
            f"Способы пополнения ещё подключаются. Пока можно на сайте: {SITE_URL}/v2#topup",
            reply_markup=back_to_menu_kb(), parse_mode="HTML",
        )
        return
    rows = []
    for m in enabled:
        label, icon = _METHODS[m]
        rows.append([InlineKeyboardButton(text=label, callback_data=f"topup:go:{m}:{amount}",
                                          icon_custom_emoji_id=eid(icon))])
    rows.append([InlineKeyboardButton(text="◁  Назад", callback_data="topup:start",
                                      icon_custom_emoji_id=eid("home"))])
    await msg.answer(
        f"{pe('wallet')}  <b>Пополнение на {fmt_rub(amount)}</b>\n{RULE}\n\n"
        f"{pe('send')}  Выбери способ оплаты:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows), parse_mode="HTML",
    )


async def _start(target) -> None:
    msg = target if isinstance(target, Message) else target.message
    text = (
        f"{pe('money_in')}  <b>Пополнение баланса</b>\n{RULE}\n\n"
        f"{pe('wallet')}  Выбери сумму — CryptoBot, Telegram Stars ⭐ или карта/СБП.\n"
        f"{pe('check')}  Баланс общий с сайтом: пополнишь здесь — будет и на сайте.\n\n"
        f"{pe('info')}  <i>Минимум — 10 ₽ (CryptoBot, без комиссии).</i>"
    )
    if isinstance(target, CallbackQuery):
        try:
            await msg.edit_text(text, reply_markup=_amount_kb(), parse_mode="HTML")
        except Exception:
            await msg.answer(text, reply_markup=_amount_kb(), parse_mode="HTML")
        await target.answer()
    else:
        await msg.answer(text, reply_markup=_amount_kb(), parse_mode="HTML")


@router.callback_query(F.data == "topup:start")
async def cb_topup_start(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await _start(cb)


@router.callback_query(F.data == "topup:custom")
async def cb_topup_custom(cb: CallbackQuery, state: FSMContext):
    await state.set_state(TopupStates.waiting_amount)
    await cb.message.edit_text(
        f"{pe('write')}  <b>Введи сумму пополнения в рублях</b>\n{RULE}\n\n"
        f"Например: <code>500</code>.  Минимум — 50 ₽.",
        reply_markup=back_to_menu_kb(), parse_mode="HTML",
    )
    await cb.answer()


@router.message(TopupStates.waiting_amount)
async def msg_topup_amount(msg: Message, state: FSMContext):
    raw = (msg.text or "").strip().replace(" ", "").replace(",", "")
    if not raw.isdigit() or int(raw) < 10:
        await msg.answer(f"{pe('cross')}  Введи число от 10, например <code>500</code>.", parse_mode="HTML")
        return
    await state.clear()
    await _show_methods(msg, int(raw))


@router.callback_query(F.data.startswith("topup:amt:"))
async def cb_topup_amt(cb: CallbackQuery):
    try:
        amount = int(cb.data.split(":")[2])
    except (ValueError, IndexError):
        await cb.answer("Неверная сумма", show_alert=True)
        return
    await cb.answer()
    await _show_methods(cb.message, amount)


@router.callback_query(F.data.startswith("topup:go:"))
async def cb_topup_go(cb: CallbackQuery):
    parts = cb.data.split(":")
    try:
        method, amount = parts[2], int(parts[3])
    except (ValueError, IndexError):
        await cb.answer("Ошибка", show_alert=True)
        return
    await cb.answer()
    if method == "stars":
        await _create_stars(cb.message, cb.from_user.id, amount)
        return
    await _create(cb.message, cb.from_user.id, amount, method)


async def _create_stars(msg: Message, tg_id: int, amount: int) -> None:
    """Stars top-up: create the pending row on the site, then send an XTR invoice
    right here. Crediting happens in handlers/payments.py on successful_payment."""
    await typing(msg)
    try:
        r = await api.topup_create(tg_id, amount, "stars")
    except ApiError as e:
        await msg.answer(f"{pe('cross')}  Не удалось создать счёт: <i>{esc(e)}</i>",
                         reply_markup=back_to_menu_kb(), parse_mode="HTML")
        return
    tid = int(r.get("id") or 0)
    stars = int(r.get("stars") or 0)
    if tid <= 0 or stars <= 0:
        await msg.answer(f"{pe('cross')}  Сервер не вернул счёт. Попробуй ещё раз.",
                         reply_markup=back_to_menu_kb(), parse_mode="HTML")
        return
    from .payments import send_stars_invoice
    await send_stars_invoice(msg.bot, msg.chat.id, tid, stars, amount)


async def _create(msg: Message, tg_id: int, amount: int, method: str) -> None:
    await typing(msg)
    try:
        r = await api.topup_create(tg_id, amount, method)
    except ApiError as e:
        await msg.answer(f"{pe('cross')}  Не удалось создать оплату: <i>{esc(e)}</i>\n\n"
                         f"Можно пополнить на сайте: {SITE_URL}/v2#topup",
                         reply_markup=back_to_menu_kb(), parse_mode="HTML")
        return
    pay_url = r.get("pay_url") or ""
    tid = int(r.get("id") or 0)
    if not pay_url:
        await msg.answer(f"{pe('cross')}  Сервер не вернул ссылку на оплату. Попробуй ещё раз.",
                         reply_markup=back_to_menu_kb(), parse_mode="HTML")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Оплатить {amount} ₽", url=pay_url, icon_custom_emoji_id=eid("money_in"))],
        [InlineKeyboardButton(text="Проверить оплату", callback_data=f"topup:check:{tid}",
                              icon_custom_emoji_id=eid("loading"))],
        [InlineKeyboardButton(text="◁  В меню", callback_data="menu:main", icon_custom_emoji_id=eid("home"))],
    ])
    card = await msg.answer(
        f"{pe('money_in')}  <b>Счёт на {fmt_rub(amount)}</b>\n{RULE}\n\n"
        f"{pe('send')}  Нажми «Оплатить» и заверши оплату.\n"
        f"{pe('loading')}  Как оплатишь — баланс зачислится автоматически.\n\n"
        f"{pe('info')}  <i>Заказ #{tid} · я слежу за оплатой.</i>",
        reply_markup=kb, parse_mode="HTML",
    )
    asyncio.create_task(_poll(card, tg_id, tid, amount, kb))


@router.callback_query(F.data.startswith("topup:check:"))
async def cb_topup_check(cb: CallbackQuery):
    try:
        tid = int(cb.data.split(":")[2])
    except (ValueError, IndexError):
        await cb.answer("Ошибка", show_alert=True); return
    try:
        o = await api.topup_status(cb.from_user.id, tid)
    except ApiError as e:
        await cb.answer(f"Ошибка: {e}", show_alert=True); return
    st = str(o.get("status") or "")
    if st == "paid":
        await cb.message.edit_text(_paid_text(tid), reply_markup=back_to_menu_kb(), parse_mode="HTML")
        await cb.answer("Оплачено!")
    elif st in ("failed", "expired", "cancelled"):
        await cb.message.edit_text(f"{pe('cross')}  Оплата не прошла ({esc(st)}). Попробуй заново: «Пополнить».",
                                   reply_markup=back_to_menu_kb(), parse_mode="HTML")
        await cb.answer()
    else:
        await cb.answer("Оплата ещё не поступила — попробуй через минуту", show_alert=True)


def _paid_text(tid: int) -> str:
    return (
        f"{pe('party')}  <b>Баланс пополнен!</b>\n{RULE}\n\n"
        f"{pe('check')}  Платёж #{tid} зачислен.\n"
        f"{pe('money')}  Теперь можно купить Robux — /buy"
    )


async def _poll(card: Message, tg_id: int, tid: int, amount: int, kb) -> None:
    for _ in range(150):  # ~10 min
        await asyncio.sleep(4)
        try:
            o = await api.topup_status(tg_id, tid)
        except ApiError:
            continue
        st = str(o.get("status") or "")
        if st == "paid":
            try:
                await card.edit_text(_paid_text(tid), reply_markup=back_to_menu_kb(), parse_mode="HTML")
            except Exception:
                pass
            return
        if st in ("failed", "expired", "cancelled"):
            try:
                await card.edit_text(
                    f"{pe('cross')}  Оплата не прошла ({esc(st)}). Попробуй заново: «Пополнить».",
                    reply_markup=back_to_menu_kb(), parse_mode="HTML")
            except Exception:
                pass
            return
