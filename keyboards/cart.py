from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def cart_keyboard(items):
    rows = []
    for product_id, name, quantity in items:
        rows.append([
            InlineKeyboardButton(text="➖", callback_data=f"cart_dec:{product_id}"),
            InlineKeyboardButton(text=f"{name[:22]} × {quantity}", callback_data=f"product:{product_id}"),
            InlineKeyboardButton(text="➕", callback_data=f"cart_inc:{product_id}"),
        ])
    rows.append([InlineKeyboardButton(text="➕ Добавить товары", callback_data="catalog")])
    rows.append([InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="cart_clear")])
    rows.append([InlineKeyboardButton(text="📋 Оформить заявку", callback_data="order_start")])
    rows.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def empty_cart_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Открыть каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")],
    ])
