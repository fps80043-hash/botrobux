"""Show user's recent orders (Robux + shop), with tab switching."""
from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from api import ApiError, api
from keyboards import link_prompt_kb, orders_tabs_kb
from utils import esc, fmt_relative, fmt_robux, fmt_rub, status_label

router = Router(name="orders")
log = logging.getLogger(__name__)


async def _ensure_linked(target: Message | CallbackQuery) -> bool:
    tg_id = target.from_user.id
    try:
        link = await api.get_link(tg_id)
    except ApiError:
        link = None
    if not link:
        msg = target if isinstance(target, Message) else target.message
        await msg.answer(
            "🔗 Привяжи аккаунт сайта чтобы видеть свои заказы — пришли /link &lt;код&gt;.",
            reply_markup=link_prompt_kb(), parse_mode="HTML",
        )
        if isinstance(target, CallbackQuery):
            await target.answer()
        return False
    return True


def _format_robux_orders(items: list) -> str:
    if not items:
        return (
            "💎 <b>Заказы Robux</b>\n\n"
            "Пока нет заказов. Нажми «💎 Купить Robux» в меню чтобы оформить первый."
        )
    lines = ["💎 <b>Заказы Robux</b>", ""]
    for o in items[:10]:
        oid = int(o.get("id") or 0)
        amount = int(o.get("robux_amount") or 0)
        rub = int(o.get("rub_price") or 0)
        st = status_label(str(o.get("status") or ""))
        when = fmt_relative(o.get("created_at"))
        lines.append(
            f"#{oid}  ·  <b>{fmt_robux(amount)}</b>  ·  {fmt_rub(rub)}\n"
            f"   {st}  ·  <i>{esc(when)}</i>"
        )
        err = (o.get("error") or "").strip()
        if err:
            lines.append(f"   ⚠️ <i>{esc(err)}</i>")
        lines.append("")
    if len(items) > 10:
        lines.append(f"<i>… и ещё {len(items) - 10}. Полный список — на сайте.</i>")
    return "\n".join(lines)


def _format_shop_orders(items: list) -> str:
    if not items:
        return (
            "🛒 <b>Заказы магазина</b>\n\n"
            "Пока нет заказов. Загляни в /shop чтобы посмотреть товары."
        )
    lines = ["🛒 <b>Заказы магазина</b>", ""]
    for o in items[:10]:
        oid = int(o.get("id") or 0)
        title = o.get("title") or o.get("product_title") or o.get("item_title") or "Товар"
        rub = int(o.get("price_rub") or o.get("price") or 0)
        st = status_label(str(o.get("status") or ""))
        when = fmt_relative(o.get("created_at") or o.get("purchased_at"))
        lines.append(
            f"#{oid}  ·  <b>{esc(title)}</b>\n"
            f"   {fmt_rub(rub)}  ·  {st}  ·  <i>{esc(when)}</i>"
        )
        lines.append("")
    if len(items) > 10:
        lines.append(f"<i>… и ещё {len(items) - 10}. Полный список — на сайте.</i>")
    return "\n".join(lines)


async def _render_tab(target: Message | CallbackQuery, tab: str) -> None:
    msg = target if isinstance(target, Message) else target.message
    tg_id = target.from_user.id

    try:
        if tab == "shop":
            data = await api.shop_orders(tg_id, limit=20)
            items = data.get("items") or data.get("orders") or []
            text = _format_shop_orders(items)
        else:
            data = await api.robux_orders(tg_id, limit=20)
            items = data.get("items") or data.get("orders") or []
            text = _format_robux_orders(items)
    except ApiError as e:
        text = f"⚠️ Не удалось загрузить заказы: <i>{esc(e)}</i>"

    kb = orders_tabs_kb(active=tab)
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
    await _render_tab(msg, "robux")


@router.callback_query(F.data == "orders:list")
async def cb_orders_list(cb: CallbackQuery):
    if not await _ensure_linked(cb):
        return
    await _render_tab(cb, "robux")


@router.callback_query(F.data.startswith("orders:tab:"))
async def cb_orders_tab(cb: CallbackQuery):
    if not await _ensure_linked(cb):
        return
    tab = cb.data.split(":", 2)[2] if cb.data.count(":") >= 2 else "robux"
    if tab not in ("robux", "shop"):
        tab = "robux"
    await _render_tab(cb, tab)
