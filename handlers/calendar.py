import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from database import get_order
from calendar_service import create_order_event

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("calendar_add:"))
async def calendar_add(callback: CallbackQuery):
    try:
        order_id = int(callback.data.split(":", 1)[1])
    except (ValueError, AttributeError):
        await callback.answer("Некорректный номер заказа", show_alert=True)
        return

    order = await get_order(order_id)
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    try:
        link = create_order_event(order)
    except Exception:
        logger.exception("Failed to add order %s to Google Calendar", order_id)
        await callback.answer(
            "Не удалось добавить заказ в календарь. Проверьте настройки Google Calendar.",
            show_alert=True,
        )
        return

    buttons = []
    if link:
        buttons.append([InlineKeyboardButton(text="📅 Открыть в Google Calendar", url=link)])
    buttons.append([InlineKeyboardButton(text="💬 Открыть чат с клиентом", url=f"tg://user?id={order['user_id']}")])

    await callback.message.edit_reply_markup(
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer("Заказ добавлен в календарь ✓")
