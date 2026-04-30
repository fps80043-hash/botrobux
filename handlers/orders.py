"""Show user's recent Robux orders with details."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from api import ApiError, api
from keyboards import link_prompt_kb, orders_kb
from utils import esc, fmt_relative, fmt_robux, fmt_rub, status_label

router = Router(name="orders")
log = logging.getLogger(__name__)

RULE = "━━━━━━━━━━━━━━━━━━━━━━"


async def _ensure_linked(target: Message | CallbackQuery) -> bool:
    tg_id = target.from_user.id
    try:
        link = await api.get_link(tg_id)
    except ApiError:
        link = None
    if not link:
        msg = target if isinstance(target, Message) else target.message
        await msg.answer(
            "🔗  Привяжи аккаунт сайта чтобы видеть свои заказы.\n\n"
            "Получи код на сайте → Профиль → Безопасность, затем пришли <code>/link 123456</code>.",
            reply_markup=link_prompt_kb(), parse_mode="HTML",
        )
        if isinstance(target, CallbackQuery):
            await target.answer()
        return False
    return True


def _format_orders(items: list) -> str:
    if not items:
        return (
            f"📋  <b>Мои заказы Robux</b>\n"
            f"{RULE}\n\n"
            "Пока нет заказов.\n\n"
            "Нажми «💎 Купить Robux» в меню — там пресеты от 100 до 10 000 R$ "
            "и калькулятор для произвольной суммы."
        )

    # Calculate stats
    total_orders = len(items)
    total_spent = sum(int(o.get("rub_price") or 0) for o in items if str(o.get("status") or "").lower() in ("done", "completed", "paid"))
    total_robux = sum(int(o.get("robux_amount") or 0) for o in items if str(o.get("status") or "").lower() in ("done", "completed", "paid"))

    lines = [
        f"📋  <b>Мои заказы Robux</b>",
        f"{RULE}",
        "",
        f"Всего: <b>{total_orders}</b>  ·  Куплено: <b>{total_robux:,}</b> R$".replace(",", " "),
    ]
    if total_spent > 0:
        lines.append(f"Потрачено: <b>{fmt_rub(total_spent)}</b>")
    lines.append("")
    lines.append(RULE)
    lines.append("")

    for o in items[:10]:
        oid = int(o.get("id") or 0)
        amount = int(o.get("robux_amount") or 0)
        rub = int(o.get("rub_price") or 0)
        st = status_label(str(o.get("status") or ""))
        when = fmt_relative(o.get("created_at"))
        lines.append(f"<b>#{oid}</b>  ·  {fmt_robux(amount)}")
        lines.append(f"   {fmt_rub(rub)}  ·  {st}")
        lines.append(f"   <i>{esc(when)}</i>")
        err = (o.get("error") or "").strip()
        if err:
            lines.append(f"   ⚠️ <i>{esc(err)}</i>")
        gp = (o.get("gamepass_name") or "").strip()
        if gp:
            lines.append(f"   🎫 <i>{esc(gp)}</i>")
        lines.append("")

    if len(items) > 10:
        lines.append(f"<i>… и ещё {len(items) - 10}. Полный список — на сайте.</i>")
    return "\n".join(lines)


async def _render(target: Message | CallbackQuery) -> None:
    msg = target if isinstance(target, Message) else target.message
    tg_id = target.from_user.id

    try:
        data = await api.robux_orders(tg_id, limit=20)
        items = data.get("items") or data.get("orders") or []
        text = _format_orders(items)
    except ApiError as e:
        text = f"⚠️ Не удалось загрузить заказы: <i>{esc(e)}</i>"

    kb = orders_kb()
    if isinstance(target, CallbackQuery):
        try:
            await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await msg.answer(text, reply_markup=kb, parse_mode="HTML")
        await target.answer()
    else:
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(Command("orders"))
async def cmd_orders(msg: Message):
    if not await _ensure_linked(msg):
        return
    await _render(msg)


@router.callback_query(F.data == "orders:list")
async def cb_orders_list(cb: CallbackQuery):
    if not await _ensure_linked(cb):
        return
    await _render(cb)
