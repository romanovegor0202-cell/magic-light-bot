from aiogram import Router, F
from aiogram.types import CallbackQuery
from data.catalog import get_product, price_for_quantity, money
from database import get_cart, set_cart_item, clear_cart
from keyboards.cart import cart_keyboard, empty_cart_keyboard
from html import escape
from ui import replace_message

router = Router()

async def cart_payload(user_id: int):
    raw = await get_cart(user_id)
    items = []
    total_min = total_max = 0
    for row in raw:
        p = get_product(row["product_id"])
        if not p:
            continue
        q = row["quantity"]
        mn, mx = price_for_quantity(p, q)
        total_min += mn
        total_max += mx
        items.append((p["id"], p["name"], q, mn, mx))
    return items, total_min, total_max


def cart_text(items, total_min, total_max):
    if not items:
        return "🛒 <b>КОРЗИНА</b>\n\nВ корзине пока ничего нет."
    lines = ["🛒 <b>ВАША КОРЗИНА</b>", ""]
    for _, name, q, mn, mx in items:
        lines.append(f"<b>{escape(name)}</b>\nКоличество: {q}\nСтоимость: {money(mn) if mn == mx else f'от {money(mn)} до {money(mx)}'}")
        lines.append("")
    if total_min == total_max:
        lines.append(f"💰 <b>ИТОГО: {money(total_min)}</b>")
    else:
        lines.append(f"💰 <b>ИТОГО: от {money(total_min)} до {money(total_max)}</b>")
        lines.append("<i>Окончательная стоимость позиций с диапазоном согласовывается с менеджером.</i>")
    return "\n".join(lines)

async def render_cart(callback: CallbackQuery):
    items, mn, mx = await cart_payload(callback.from_user.id)
    kb_items = [(i[0], i[1], i[2]) for i in items]
    text = cart_text(items, mn, mx)
    await replace_message(callback.message, text, reply_markup=cart_keyboard(kb_items) if items else empty_cart_keyboard())

@router.callback_query(F.data == "cart")
async def show_cart(callback: CallbackQuery):
    await render_cart(callback)
    await callback.answer()

@router.callback_query(F.data.startswith("cart_inc:"))
async def inc(callback: CallbackQuery):
    pid = callback.data.split(":", 1)[1]
    raw = await get_cart(callback.from_user.id)
    current = next((x["quantity"] for x in raw if x["product_id"] == pid), 0)
    p = get_product(pid)
    if not p:
        await callback.answer("Товар не найден", show_alert=True); return
    max_qty = p.get("pricing", {}).get("max_quantity")
    new_q = current + 1
    if max_qty and new_q > max_qty:
        await callback.answer("Для этой позиции доступно только 1 оформление", show_alert=True)
        return
    await set_cart_item(callback.from_user.id, pid, new_q)
    await render_cart(callback)
    await callback.answer()

@router.callback_query(F.data.startswith("cart_dec:"))
async def dec(callback: CallbackQuery):
    pid = callback.data.split(":", 1)[1]
    raw = await get_cart(callback.from_user.id)
    current = next((x["quantity"] for x in raw if x["product_id"] == pid), 0)
    await set_cart_item(callback.from_user.id, pid, current - 1)
    await render_cart(callback)
    await callback.answer()

@router.callback_query(F.data == "cart_clear")
async def cart_clear(callback: CallbackQuery):
    await clear_cart(callback.from_user.id)
    await render_cart(callback)
    await callback.answer("Корзина очищена")
