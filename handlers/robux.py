"""Robux purchase flow: stock, quote, presets, custom amount, in-bot buy."""
from __future__ import annotations

import asyncio
import logging
import re

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from api import ApiError, api
from config import SITE_URL
from keyboards import back_to_menu_kb, link_prompt_kb, orders_kb, robux_amount_kb, robux_confirm_kb
from premoji import pe
from utils import bar, esc, fmt_num, fmt_robux, fmt_rub, typing

router = Router(name="robux")
log = logging.getLogger(__name__)


RULE = "━━━━━━━━━━━━━━━━━━━━━━"


class RobuxStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_recipient = State()


async def _ensure_linked(target: Message | CallbackQuery) -> bool:
    tg_id = target.from_user.id
    try:
        link = await api.get_link(tg_id)
    except ApiError:
        link = None
    if not link:
        msg = target if isinstance(target, Message) else target.message
        await msg.answer(
            "🔗 <b>Сначала привяжи аккаунт</b>\n\n"
            "Получи код на сайте → Профиль → Безопасность → Telegram-бот, "
            "затем пришли:  <code>/link 123456</code>",
            reply_markup=link_prompt_kb(), parse_mode="HTML",
        )
        if isinstance(target, CallbackQuery):
            await target.answer()
        return False
    return True


def _stock_indicator(avail: int) -> tuple[str, str]:
    """Returns (emoji, text) describing stock level."""
    if avail >= 10000:
        return "🟢", "много в наличии"
    if avail >= 1000:
        return "🟡", "средний запас"
    if avail > 0:
        return "🟠", "мало"
    return "🔴", "временно нет"


async def _render_start(target: Message | CallbackQuery) -> None:
    msg = target if isinstance(target, Message) else target.message
    await typing(target)

    try:
        stock = await api.robux_stock()
    except ApiError as e:
        log.warning("robux_stock failed: %s", e)
        stock = {}

    avail = int(stock.get("available") or stock.get("stock") or 0)
    rate = stock.get("rate")
    stock_emo, stock_txt = _stock_indicator(avail)

    rate_str = ""
    if rate:
        try:
            rate_str = f"<b>{float(rate):.2f}</b> ₽ за 1 R$"
        except (TypeError, ValueError):
            rate_str = ""

    # Try also showing current balance for context
    try:
        bal = await api.get_balance(target.from_user.id)
        balance_line = f"{pe('wallet')}  Твой баланс:  <b>{fmt_rub(bal)}</b>\n"
    except ApiError:
        balance_line = ""

    text = (
        f"{pe('money')}  <b>Покупка Robux</b>\n"
        f"{RULE}\n\n"
        f"{stock_emo}  В наличии:  <b>{fmt_num(avail)} R$</b>  <i>({stock_txt})</i>\n"
    )
    if rate_str:
        text += f"{pe('stats')}  Курс:  {rate_str}\n"
    text += balance_line
    text += (
        f"\n{RULE}\n"
        f"{pe('write')}  Выбери сумму или введи свою. Минимум — <b>50 R$</b>.\n\n"
        f"{pe('clock')}  Доставка: ~5–15 минут\n"
        f"{pe('lock')}  Безопасно: через геймпасс\n"
        f"{pe('check')}  Гарантия возврата средств\n\n"
        f"{pe('bot')}  <i>Оформить можно прямо здесь — нажми сумму.</i>"
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
@router.callback_query(F.data == "robux:refresh")
async def cb_robux_start(cb: CallbackQuery, state: FSMContext):
    if not await _ensure_linked(cb):
        return
    await state.clear()
    await _render_start(cb)


async def _show_quote(target: Message | CallbackQuery, amount: int) -> None:
    msg = target if isinstance(target, Message) else target.message
    if amount < 50:
        await msg.answer(
            "❌ Минимальная сумма — <b>50 R$</b>. Выбери побольше.",
            reply_markup=robux_amount_kb(), parse_mode="HTML",
        )
        if isinstance(target, CallbackQuery):
            await target.answer()
        return

    # Animated loading: typing action + an intermediate "calculating" card the
    # final result replaces — feels alive instead of a frozen pause.
    await typing(target)
    if isinstance(target, CallbackQuery):
        try:
            await msg.edit_text(
                f"⏳  Считаю цену для <b>{fmt_robux(amount)}</b>…",
                parse_mode="HTML",
            )
        except Exception:
            pass

    try:
        balance = await api.get_balance(target.from_user.id)
    except ApiError:
        balance = 0

    try:
        quote = await api.robux_quote(amount)
    except ApiError as e:
        await msg.answer(
            f"⚠️ Не удалось рассчитать цену: <i>{esc(e)}</i>",
            parse_mode="HTML",
        )
        if isinstance(target, CallbackQuery):
            await target.answer()
        return

    rub_price = int(quote.get("rub_price") or quote.get("price") or 0)
    gp_amount = quote.get("gamepass_robux") or quote.get("gamepass_price") or amount
    rate = quote.get("rate")
    can_pay = balance >= rub_price

    lines = [
        f"{pe('money')}  <b>{fmt_robux(amount)}</b>",
        f"{RULE}",
        "",
        f"{pe('money_out')}  <b>К оплате:</b>  {fmt_rub(rub_price)}",
    ]
    if rate:
        try:
            lines.append(f"{pe('stats')}  Курс:  <b>{float(rate):.2f}</b> ₽/R$")
        except (TypeError, ValueError):
            pass
    if gp_amount and int(gp_amount) != amount:
        lines.append(f"{pe('tag')}  Геймпасс:  <b>{fmt_num(gp_amount)} R$</b>  <i>(с комиссией Roblox)</i>")
    lines.append("")
    lines.append(f"{pe('wallet')}  Баланс:  <b>{fmt_rub(balance)}</b>")
    if rub_price > 0:
        pct = min(100, int(balance * 100 / rub_price))
        lines.append(f"<code>{bar(balance, rub_price)}</code>  {pct}%")
    lines.append("")
    lines.append(RULE)

    if can_pay:
        remaining = balance - rub_price
        lines.append(f"{pe('check')}  <b>Баланса хватает</b>")
        lines.append(f"После покупки останется:  <b>{fmt_rub(remaining)}</b>")
        lines.append("")
        lines.append(f"{pe('lock')}  Жми «Купить» — введёшь ник или ссылку на геймпасс.")
    else:
        diff = rub_price - balance
        lines.append(f"{pe('cross')}  <b>Не хватает:  {fmt_rub(diff)}</b>")
        lines.append("")
        lines.append(f"{pe('wallet')}  Сначала пополни баланс, затем возвращайся.")

    text = "\n".join(lines)
    if isinstance(target, CallbackQuery):
        try:
            await msg.edit_text(text, reply_markup=robux_confirm_kb(amount, can_pay), parse_mode="HTML")
        except Exception:
            await msg.answer(text, reply_markup=robux_confirm_kb(amount, can_pay), parse_mode="HTML")
        await target.answer()
    else:
        await msg.answer(text, reply_markup=robux_confirm_kb(amount, can_pay), parse_mode="HTML")


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
        "✏️  <b>Введи количество Robux</b>\n"
        f"{RULE}\n\n"
        "Просто отправь число — например, <code>2500</code>.\n\n"
        "📏  Лимиты:\n"
        "•  Минимум — <b>50 R$</b>\n"
        "•  Максимум — <b>50 000 R$</b>\n\n"
        "<i>Чтобы отменить — нажми /menu или кнопку ниже.</i>"
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


# ─────────────────────────── In-bot purchase ───────────────────────────

@router.callback_query(F.data.startswith("robux:buy:"))
async def cb_robux_buy(cb: CallbackQuery, state: FSMContext):
    """Start the in-bot buy: ask the recipient (nick or gamepass link)."""
    if not await _ensure_linked(cb):
        return
    try:
        amount = int(cb.data.split(":")[2])
    except (ValueError, IndexError):
        await cb.answer("Неверная сумма", show_alert=True)
        return
    await state.set_state(RobuxStates.waiting_for_recipient)
    await state.update_data(amount=amount)
    text = (
        f"{pe('bot')}  <b>Куда зачислить {fmt_robux(amount)}</b>\n"
        f"{RULE}\n\n"
        f"{pe('write')}  Пришли <b>ник Roblox</b> или <b>ссылку на геймпасс</b>:\n\n"
        f"• <code>Builderman</code>  — найду твой геймпасс сам\n"
        f"• <code>roblox.com/game-pass/123…</code>  — если уже создал\n\n"
        f"{pe('info')}  <i>Геймпасс должен быть на нужную сумму и выставлен на продажу.</i>"
    )
    try:
        await cb.message.edit_text(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
    except Exception:
        await cb.message.answer(text, reply_markup=back_to_menu_kb(), parse_mode="HTML")
    await cb.answer()


@router.message(RobuxStates.waiting_for_recipient)
async def msg_recipient(msg: Message, state: FSMContext):
    data = await state.get_data()
    amount = int(data.get("amount") or 0)
    await state.clear()
    if amount <= 0:
        await msg.answer("Что-то пошло не так — начни заново: /buy")
        return

    raw = (msg.text or "").strip()
    nick, url = "", ""
    if re.search(r"roblox\.com/game-pass/\d+", raw, re.I) or raw.isdigit():
        url = raw
    else:
        cand = raw.lstrip("@")
        if re.fullmatch(r"[A-Za-z0-9_]{3,25}", cand):
            nick = cand
        else:
            await msg.answer(
                f"{pe('cross')}  Не похоже на ник или ссылку.\n"
                "Ник — латиница/цифры/_ (3–25), или ссылка на геймпасс.",
                parse_mode="HTML",
            )
            await state.set_state(RobuxStates.waiting_for_recipient)
            await state.update_data(amount=amount)
            return

    tg_id = msg.from_user.id
    await typing(msg)
    progress = await msg.answer(
        f"{pe('loading')}  <b>Оформляю заказ</b>\n{RULE}\n\n"
        f"{pe('eye')}  Ищу геймпасс на <b>{fmt_robux(amount)}</b>…\n\n"
        f"<i>Если по нику — поиск может занять до минуты.</i>",
        parse_mode="HTML",
    )

    # Create the order in the background and animate while it runs (the by-nick
    # gamepass scan can take 10–60s — don't leave a frozen message).
    order_task = asyncio.create_task(api.robux_order(tg_id, amount, nick=nick, url=url))
    i = 0
    while not order_task.done():
        spin = _SPIN[i % len(_SPIN)]
        try:
            await progress.edit_text(
                f"{spin}  <b>Оформляю заказ</b>\n{RULE}\n\n"
                f"{pe('eye')}  Ищу геймпасс на <b>{fmt_robux(amount)}</b>…\n\n"
                f"<i>Поиск по нику бывает дольше.</i>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await asyncio.sleep(1.6)
        i += 1
    try:
        res = order_task.result()
    except ApiError as e:
        await progress.edit_text(
            f"{pe('cross')}  <b>Не удалось оформить</b>\n{RULE}\n\n<i>{esc(e)}</i>\n\n"
            f"{pe('info')}  Проверь геймпасс/ник и баланс, затем попробуй снова: /buy",
            reply_markup=back_to_menu_kb(), parse_mode="HTML",
        )
        return
    except Exception as e:
        await progress.edit_text(
            f"{pe('cross')}  Ошибка: <i>{esc(e)}</i>\n\nПопробуй снова: /buy",
            reply_markup=back_to_menu_kb(), parse_mode="HTML",
        )
        return

    oid = int(res.get("order_id") or 0)
    if oid <= 0:
        await progress.edit_text(f"{pe('cross')} Сервер не вернул номер заказа. Попробуй ещё раз.",
                                 reply_markup=back_to_menu_kb(), parse_mode="HTML")
        return

    await _poll_order(progress, tg_id, oid, amount, nick or url)


_SPIN = ["◐", "◓", "◑", "◒"]


async def _poll_order(progress: Message, tg_id: int, oid: int, amount: int, recipient: str) -> None:
    """Animate while the delivery worker runs; show final result."""
    stages = [
        f"{pe('lock')}  Бронирую и списываю с баланса…",
        f"{pe('bot')}  Покупаю геймпасс на Roblox…",
        f"{pe('money')}  Зачисляю Robux на аккаунт…",
        f"{pe('loading')}  Почти готово…",
    ]
    miss_streak = 0
    for i in range(170):  # ~6-7 min — delivery can retry several times
        try:
            o = await api.robux_order_status(tg_id, oid)
            miss_streak = 0
        except ApiError as e:
            o = {}
            # Persistent fetch failure (e.g. order_status 404) — don't fake-spin
            # for 6 minutes. After ~30s of misses, hand off to /orders.
            if getattr(e, "status", 0) in (404, 400):
                miss_streak += 1
                if miss_streak >= 15:
                    await progress.edit_text(
                        f"{pe('clock')}  Заказ <code>#{oid}</code> оформлен, но статус пока не подтянулся.\n"
                        "Проверь его в /orders — деньги защищены (вернутся при сбое).",
                        reply_markup=orders_kb(), parse_mode="HTML",
                    )
                    return
        st = str(o.get("status") or "")

        if st == "done":
            await progress.edit_text(
                f"{pe('party')}  <b>Готово! Robux зачислены</b>\n{RULE}\n\n"
                f"{pe('money')}  Сумма:  <b>{fmt_robux(amount)}</b>\n"
                f"{pe('check')}  Заказ:  <code>#{oid}</code>\n"
                f"{pe('profile')}  Аккаунт:  <b>{esc(recipient)}</b>\n\n"
                f"{pe('smile')}  Спасибо за покупку!",
                reply_markup=orders_kb(), parse_mode="HTML",
            )
            return
        if st in ("failed", "cancelled", "expired", "error"):
            err = esc(o.get("error") or "")
            await progress.edit_text(
                f"{pe('cross')}  <b>Заказ не выполнен</b>  ({esc(st)})\n{RULE}\n\n"
                + (f"<i>{err}</i>\n\n" if err else "")
                + f"{pe('info')}  Если деньги списались — они <b>возвращены на баланс</b> автоматически.\n"
                  f"Заказ <code>#{oid}</code> — детали в /orders.",
                reply_markup=back_to_menu_kb(), parse_mode="HTML",
            )
            return

        spin = _SPIN[i % len(_SPIN)]
        stage = stages[min(i // 4, len(stages) - 1)]
        # Progress bar fills gradually (caps ~95% until done so it never lies).
        prog = min(95, 8 + i * 4)
        try:
            await progress.edit_text(
                f"{spin}  <b>Заказ #{oid}</b>\n{RULE}\n\n"
                f"{stage}\n\n"
                f"<code>{bar(prog, 100)}</code>  {prog}%\n\n"
                f"{pe('info')}  <i>Обычно 5–60 секунд.</i>",
                parse_mode="HTML",
            )
        except Exception:
            pass
        await asyncio.sleep(2)

    await progress.edit_text(
        f"{pe('clock')}  Заказ <code>#{oid}</code> ещё выполняется дольше обычного.\n"
        "Статус появится в /orders — деньги защищены (вернутся при сбое).",
        reply_markup=orders_kb(), parse_mode="HTML",
    )
