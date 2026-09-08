from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Открыть каталог", callback_data="catalog")],
        [InlineKeyboardButton(text="🛒 Моя корзина", callback_data="cart")],
        [InlineKeyboardButton(text="👨‍💼 Связаться с менеджером", callback_data="manager")],
        [InlineKeyboardButton(text="ℹ️ О компании", callback_data="about")],
    ])


def back_home():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⌂ Главное меню", callback_data="home")]
    ])
