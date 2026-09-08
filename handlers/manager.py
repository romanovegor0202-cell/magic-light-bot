from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import get_settings
from ui import replace_message

router = Router()

@router.callback_query(F.data == "manager")
async def manager(callback: CallbackQuery):
    settings = get_settings()
    text = (
        "👨‍💼 <b>СВЯЗАТЬСЯ С МЕНЕДЖЕРОМ</b>\n\n"
        "Если хотите уточнить детали, задать вопрос или обсудить заказ — свяжитесь с нами напрямую.\n\n"
    )
    if settings.manager_phone:
        text += f"📞 Телефон: {settings.manager_phone}\n"
    buttons = []
    if settings.manager_username:
        buttons.append([InlineKeyboardButton(text="💬 Написать менеджеру", url=f"https://t.me/{settings.manager_username}")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")])
    await replace_message(callback.message, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()

@router.callback_query(F.data == "about")
async def about(callback: CallbackQuery):
    settings = get_settings()
    text = (
        f"✨ <b>{settings.company_name}</b>\n\n"
        "Студия свадебных спецэффектов.\n\n"
        "Создаём эффектные и запоминающиеся моменты для свадеб, торжеств и других мероприятий.\n\n"
        "Все цены представлены в каталоге. Для сложных шоу и нестандартных задач окончательные условия согласовываются с менеджером."
    )
    buttons = []
    if settings.manager_username:
        buttons.append([InlineKeyboardButton(text="👨‍💼 Связаться с менеджером", url=f"https://t.me/{settings.manager_username}")])
    buttons.append([InlineKeyboardButton(text="🛍 Каталог", callback_data="catalog")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")])
    await replace_message(callback.message, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()
