"""Browse the shop catalog grouped by category. Read-only — purchase on the site."""
from __future__ import annotations

import logging
from collections import OrderedDict

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from api import ApiError, api
from config import SITE_URL
from keyboards import back_to_menu_kb
from utils import esc, fmt_rub

router = Router(name="shop")
log = logging.getLogger(__name__)


def _group_items_by_category(items: list, categories: list) -> "OrderedDict[str, dict]":
    """Group items by their category_id, preserving the catalog's category order."""
    cat_titles = {str(c.get("id")): str(c.get("title") or c.get("id") or "") for c in (categories or [])}
    cat_order = [str(c.get("id")) for c in (categories or []) if c.get("visible") is not False]

    grouped: "OrderedDict[str, dict]" = OrderedDict()
    for cid in cat_order:
        grouped[cid] = {"title": cat_titles.get(cid, cid), "items": []}

    for item in items or []:
        if item.get("visible") is False:
            continue
        raw = item.get("raw") or {}
        cid = str(raw.get("category_id") or item.get("category") or "other")
        if cid not in grouped:
            grouped[cid] = {"title": cat_titles.get(cid, cid or "Прочее"), "items": []}
        grouped[cid]["items"].append(item)

    # Drop empty categories
    return OrderedDict((k, v) for k, v in grouped.items() if v["items"])


def _categories_kb(grouped: "OrderedDict[str, dict]") -> InlineKeyboardMarkup:
    rows = []
    line = []
    for cid, data in grouped.items():
        title = data["title"][:24]
        count = len(data["items"])
        line.append(InlineKeyboardButton(
            text=f"{title} · {count}",
            callback_data=f"shop:cat:{cid}",
        ))
        if len(line) == 2:
            rows.append(line)
            line = []
    if line:
        rows.append(line)
    rows.append([InlineKeyboardButton(text="🌐 Открыть на сайте", url=f"{SITE_URL}/v2")])
    rows.append([InlineKeyboardButton(text="‹ В меню", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _format_category_items(category_title: str, items: list) -> str:
    lines = [f"🛒 <b>{esc(category_title)}</b>", ""]
    for item in items[:25]:
        title = str(item.get("title") or "Товар")
        price = float(item.get("price") or 0)
        raw = item.get("raw") or {}
        oos = bool(raw.get("out_of_stock"))
        line = f"• <b>{esc(title)}</b>  —  {fmt_rub(int(price))}"
        if oos:
            line += "  ⚠️ <i>нет в наличии</i>"
        lines.append(line)
        desc = str(item.get("description") or "").strip()
        if desc:
            short = desc[:120] + ("…" if len(desc) > 120 else "")
            lines.append(f"   <i>{esc(short)}</i>")
    if len(items) > 25:
        lines.append("")
        lines.append(f"<i>… и ещё {len(items) - 25} в этой категории. Все товары — на сайте.</i>")
    lines.append("")
    lines.append(f"💳 Покупка — на сайте: {SITE_URL}/v2")
    return "\n".join(lines)


def _category_back_kb(grouped_keys: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌐 На сайт", url=f"{SITE_URL}/v2")],
        [
            InlineKeyboardButton(text="‹ К категориям", callback_data="shop:list"),
            InlineKeyboardButton(text="В меню", callback_data="menu:main"),
        ],
    ])


@router.message(Command("shop"))
async def cmd_shop(msg: Message):
    await _show_categories(msg)


@router.callback_query(F.data == "shop:list")
async def cb_shop_list(cb: CallbackQuery):
    await _show_categories(cb)


async def _show_categories(target: Message | CallbackQuery) -> None:
    msg = target if isinstance(target, Message) else target.message

    try:
        data = await api.shop_catalog()
    except ApiError as e:
        await msg.answer(f"⚠️ Не удалось загрузить каталог: <i>{esc(e)}</i>", parse_mode="HTML")
        if isinstance(target, CallbackQuery):
            await target.answer()
        return

    items = data.get("items") or []
    cfg = data.get("config") or {}
    categories = cfg.get("categories") or []
    grouped = _group_items_by_category(items, categories)

    if not grouped:
        text = (
            "🛒 <b>Каталог</b>\n\n"
            "Сейчас нет доступных категорий. Загляни попозже или открой сайт."
        )
        kb = back_to_menu_kb()
    else:
        total_items = sum(len(v["items"]) for v in grouped.values())
        text = (
            "🛒 <b>Каталог магазина</b>\n\n"
            f"Категорий: <b>{len(grouped)}</b>  ·  Товаров: <b>{total_items}</b>\n\n"
            "Выбери категорию:"
        )
        kb = _categories_kb(grouped)

    if isinstance(target, CallbackQuery):
        try:
            await msg.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await msg.answer(text, reply_markup=kb, parse_mode="HTML")
        await target.answer()
    else:
        await msg.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("shop:cat:"))
async def cb_shop_category(cb: CallbackQuery):
    cid = cb.data.split(":", 2)[2] if cb.data.count(":") >= 2 else ""
    if not cid:
        await cb.answer()
        return

    try:
        data = await api.shop_catalog()
    except ApiError as e:
        await cb.answer(f"Ошибка: {e}", show_alert=True)
        return

    items = data.get("items") or []
    cfg = data.get("config") or {}
    categories = cfg.get("categories") or []
    grouped = _group_items_by_category(items, categories)

    cat = grouped.get(cid)
    if not cat:
        await cb.answer("Категория не найдена", show_alert=True)
        return

    text = _format_category_items(cat["title"], cat["items"])
    kb = _category_back_kb(list(grouped.keys()))
    try:
        await cb.message.edit_text(text, reply_markup=kb, parse_mode="HTML",
                                   disable_web_page_preview=True)
    except Exception:
        await cb.message.answer(text, reply_markup=kb, parse_mode="HTML",
                                disable_web_page_preview=True)
    await cb.answer()
