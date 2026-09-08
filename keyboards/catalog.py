from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from data.catalog import CATEGORIES, get_products_by_category

CATEGORY_ICONS = {
    "Тяжёлый дым": "🌫",
    "Холодные фонтаны": "✨",
    "Вертушки с фонтанами": "🎇",
    "Огнепад": "🔥",
    "Огненное сердце": "❤️",
    "Бенгальские огни": "✦",
    "Дневные цветные дымовые залпы": "🌈",
    "Конфетти-пушка": "🎉",
    "Дневные веерные салюты": "🎆",
    "Дневные салюты «Лапша»": "🎆",
    "Большой воздушный шар": "🎈",
    "«Дымные» мыльные пузыри": "🫧",
    "Крио-пушка": "❄️",
    "Ночные салюты": "🌙",
}


def categories_keyboard():
    rows = []
    for i, cat in enumerate(CATEGORIES):
        icon = CATEGORY_ICONS.get(cat, "✨")
        rows.append([InlineKeyboardButton(text=f"{icon} {cat}", callback_data=f"cat:{i}")])
    rows.append([InlineKeyboardButton(text="⌂ Главное меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def products_keyboard(category: str):
    products = get_products_by_category(category)
    rows = []
    for p in products:
        rows.append([InlineKeyboardButton(text=p['name'], callback_data=f"product:{p['id']}")])
    rows.append([InlineKeyboardButton(text="‹ Все категории", callback_data="catalog")])
    rows.append([InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def product_keyboard(product_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="＋ Добавить в корзину", callback_data=f"add:{product_id}")],
        [InlineKeyboardButton(text="‹ Назад к категории", callback_data=f"back_product:{product_id}")],
        [InlineKeyboardButton(text="🛒 Открыть корзину", callback_data="cart")],
    ])
