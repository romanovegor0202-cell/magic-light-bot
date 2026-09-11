from aiogram import Router, F
from aiogram.types import CallbackQuery
from keyboards.catalog import categories_keyboard, products_keyboard, product_keyboard
from catalog_data.catalog import CATEGORIES, get_product, get_products_by_category, price_label
from html import escape
from ui import replace_message

router = Router()

@router.callback_query(F.data == "catalog")
async def catalog(callback: CallbackQuery):
    text = "🛍 <b>КАТАЛОГ ЭФФЕКТОВ</b>\n\nВыберите эффект, чтобы посмотреть фото, описание и стоимость."
    await replace_message(callback.message, text, reply_markup=categories_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("cat:"))
async def category(callback: CallbackQuery):
    idx = int(callback.data.split(":", 1)[1])
    if idx >= len(CATEGORIES):
        await callback.answer("Категория не найдена", show_alert=True)
        return
    cat = CATEGORIES[idx]
    text = f"✨ <b>{escape(cat)}</b>\n\nВыберите вариант, чтобы открыть подробности:"
    await replace_message(callback.message, text, reply_markup=products_keyboard(cat))
    await callback.answer()

@router.callback_query(F.data.startswith("product:"))
async def product(callback: CallbackQuery):
    product_id = callback.data.split(":", 1)[1]
    p = get_product(product_id)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return
    text = (
        f"<b>{escape(p['name'])}</b>\n\n"
        f"{escape(p['description'])}\n\n"
        f"💰 <b>Стоимость:</b>\n{escape(price_label(p))}"
    )
    path = p.get("image")
    try:
        from aiogram.types import FSInputFile
        await callback.message.delete()
        await callback.message.answer_photo(FSInputFile(str(__import__("pathlib").Path(__file__).resolve().parent.parent / path)), caption=text, reply_markup=product_keyboard(product_id))
    except Exception:
        await callback.message.edit_text(text, reply_markup=product_keyboard(product_id))
    await callback.answer()

@router.callback_query(F.data.startswith("back_product:"))
async def back_product(callback: CallbackQuery):
    product_id = callback.data.split(":", 1)[1]
    p = get_product(product_id)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return
    await replace_message(callback.message, f"✨ <b>{escape(p['category'])}</b>\n\nВыберите спецэффект:", reply_markup=products_keyboard(p["category"]))
    await callback.answer()

@router.callback_query(F.data.startswith("add:"))
async def add(callback: CallbackQuery):
    from database import get_cart, set_cart_item
    product_id = callback.data.split(":", 1)[1]
    p = get_product(product_id)
    if not p:
        await callback.answer("Товар не найден", show_alert=True)
        return
    current = next((x["quantity"] for x in await get_cart(callback.from_user.id) if x["product_id"] == product_id), 0)
    max_qty = p.get("pricing", {}).get("max_quantity")
    new_qty = current + 1
    if max_qty and new_qty > max_qty:
        new_qty = max_qty
    await set_cart_item(callback.from_user.id, product_id, new_qty)
    await callback.answer("Добавлено в корзину ✓")
