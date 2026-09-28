import json
from html import escape

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

from config import get_settings
from database import get_cart, create_order, clear_cart
from catalog_data.catalog import get_product, price_for_quantity, money
from keyboards.order import phone_keyboard, skip_keyboard, confirm_keyboard
from keyboards.main import main_menu

router = Router()

class OrderForm(StatesGroup):
    name = State()
    phone = State()
    event_date = State()
    venue = State()
    comment = State()
    confirm = State()


def totals_and_items(raw_cart):
    items = []
    total_min = total_max = 0
    for row in raw_cart:
        p = get_product(row["product_id"])
        if not p:
            continue
        q = row["quantity"]
        mn, mx = price_for_quantity(p, q)
        total_min += mn
        total_max += mx
        items.append({
            "id": p["id"], "name": p["name"], "quantity": q,
            "unit_price": mn if mn == mx else None,
            "line_min": mn, "line_max": mx,
        })
    return items, total_min, total_max


def order_summary(data, items, total_min, total_max):
    lines = ["📋 <b>ПРОВЕРЬТЕ ЗАЯВКУ</b>", ""]
    lines += [
        f"👤 <b>Имя:</b> {escape(data['name'])}",
        f"📞 <b>Телефон:</b> {escape(data['phone'])}",
        f"📅 <b>Дата:</b> {escape(data['event_date'])}",
        f"📍 <b>Место:</b> {escape(data['venue'])}",
        "",
        "🛒 <b>ЗАКАЗ:</b>",
    ]
    for item in items:
        if item["line_min"] == item["line_max"]:
            lines.append(f"• {escape(item['name'])} — {item['quantity']} × = <b>{money(item['line_min'])}</b>")
        else:
            lines.append(f"• {escape(item['name'])} — {item['quantity']} × = <b>от {money(item['line_min'])} до {money(item['line_max'])}</b>")
    lines += ["", f"💰 <b>ИТОГО: {money(total_min) if total_min == total_max else f'от {money(total_min)} до {money(total_max)}'}</b>"]
    if data.get("comment"):
        lines += ["", f"💬 <b>Комментарий:</b> {escape(data['comment'])}"]
    return "\n".join(lines)


def manager_keyboard(user_id: int, order_id: int):
    settings = get_settings()
    rows = []

    if settings.manager_username:
        rows.append([
            InlineKeyboardButton(
                text="💬 Написать менеджеру",
                url=f"https://t.me/{settings.manager_username}"
            )
        ])

    rows.append([
        InlineKeyboardButton(
            text="💬 Открыть чат с клиентом",
            url=f"tg://user?id={user_id}"
        )
    ])

    rows.append([
        InlineKeyboardButton(
            text="📅 Добавить в Google Calendar",
            callback_data=f"calendar_add:{order_id}"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)

@router.callback_query(F.data == "order_start")
async def order_start(callback: CallbackQuery, state: FSMContext):
    raw = await get_cart(callback.from_user.id)
    items, _, _ = totals_and_items(raw)
    if not items:
        await callback.answer("Корзина пустая", show_alert=True)
        return
    await state.clear()
    await state.set_state(OrderForm.name)
    await callback.message.edit_text("👤 <b>Как вас зовут?</b>\n\nВведите имя.")
    await callback.answer()

@router.message(OrderForm.name)
async def order_name(message: Message, state: FSMContext):
    value = message.text.strip() if message.text else ""
    if len(value) < 2:
        await message.answer("Пожалуйста, укажите имя.")
        return
    await state.update_data(name=value)
    await state.set_state(OrderForm.phone)
    await message.answer("📞 <b>Оставьте номер телефона</b>\n\nНажмите кнопку ниже или введите номер вручную.", reply_markup=phone_keyboard())

@router.message(OrderForm.phone, F.contact)
async def order_phone_contact(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(OrderForm.event_date)
    await message.answer("📅 <b>Дата мероприятия</b>\n\nВведите дату, например: 20.09.2026", reply_markup=ReplyKeyboardRemove())

@router.message(OrderForm.phone)
async def order_phone_text(message: Message, state: FSMContext):
    value = message.text.strip() if message.text else ""
    digits = ''.join(ch for ch in value if ch.isdigit())
    if len(digits) < 10:
        await message.answer("Введите корректный номер телефона, например +7 909 302-04-34.")
        return
    await state.update_data(phone=value)
    await state.set_state(OrderForm.event_date)
    await message.answer("📅 <b>Дата мероприятия</b>\n\nВведите дату, например: 20.09.2026", reply_markup=ReplyKeyboardRemove())

@router.message(OrderForm.event_date)
async def order_date(message: Message, state: FSMContext):
    value = message.text.strip() if message.text else ""
    if len(value) < 4:
        await message.answer("Укажите дату мероприятия.")
        return
    await state.update_data(event_date=value)
    await state.set_state(OrderForm.venue)
    await message.answer("📍 <b>Где будет проходить мероприятие?</b>\n\nУкажите город и площадку/ресторан.")

@router.message(OrderForm.venue)
async def order_venue(message: Message, state: FSMContext):
    value = message.text.strip() if message.text else ""
    if len(value) < 2:
        await message.answer("Укажите место проведения.")
        return
    await state.update_data(venue=value)
    await state.set_state(OrderForm.comment)
    await message.answer("💬 <b>Есть дополнительные пожелания?</b>\n\nНапишите их или нажмите «Пропустить».", reply_markup=skip_keyboard())

@router.message(OrderForm.comment)
async def order_comment(message: Message, state: FSMContext):
    value = message.text.strip() if message.text else ""
    await state.update_data(comment=value)
    await show_confirmation(message, state)

@router.callback_query(OrderForm.comment, F.data == "order_skip_comment")
async def order_skip_comment(callback: CallbackQuery, state: FSMContext):
    await state.update_data(comment="")
    await show_confirmation(callback.message, state, edit=True)
    await callback.answer()

async def show_confirmation(message, state: FSMContext, edit=False):
    data = await state.get_data()
    raw = await get_cart(message.chat.id)
    items, total_min, total_max = totals_and_items(raw)
    if not items:
        await state.clear()
        if edit:
            await message.edit_text("🛒 Корзина пуста.")
        else:
            await message.answer("🛒 Корзина пуста.")
        return
    await state.update_data(items=items, total_min=total_min, total_max=total_max)
    text = order_summary(data, items, total_min, total_max)
    await state.set_state(OrderForm.confirm)
    if edit:
        await message.edit_text(text, reply_markup=confirm_keyboard())
    else:
        await message.answer(text, reply_markup=confirm_keyboard())

@router.callback_query(OrderForm.confirm, F.data == "order_cancel")
async def order_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ <b>Оформление заявки отменено.</b>\n\nКорзина сохранена — вы можете вернуться к ней из главного меню.", reply_markup=main_menu())
    await callback.answer()

@router.callback_query(OrderForm.confirm, F.data == "order_confirm")
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])
    if not items:
        await callback.answer("Корзина пуста", show_alert=True)
        return
    total_min = data["total_min"]
    total_max = data["total_max"]
    order_id = await create_order(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        name=data["name"],
        phone=data["phone"],
        event_date=data["event_date"],
        venue=data["venue"],
        comment=data.get("comment", ""),
        items_json=json.dumps(items, ensure_ascii=False),
        total_min=total_min,
        total_max=total_max,
    )

    settings = get_settings()
    manager_lines = [
        f"🔔 <b>НОВАЯ ЗАЯВКА {escape(settings.company_name)}</b>",
        f"<b>№ {order_id}</b>", "",
        f"👤 <b>Клиент:</b> {escape(data['name'])}",
        f"📞 <b>Телефон:</b> {escape(data['phone'])}",
        f"📅 <b>Дата:</b> {escape(data['event_date'])}",
        f"📍 <b>Место:</b> {escape(data['venue'])}",
    ]
    if callback.from_user.username:
        manager_lines.append(f"Telegram: @{escape(callback.from_user.username)}")
    manager_lines += ["", "🛒 <b>ЗАКАЗ:</b>"]
    for item in items:
        if item["line_min"] == item["line_max"]:
            manager_lines.append(f"• {escape(item['name'])} — {item['quantity']} × = <b>{money(item['line_min'])}</b>")
        else:
            manager_lines.append(f"• {escape(item['name'])} — {item['quantity']} × = <b>от {money(item['line_min'])} до {money(item['line_max'])}</b>")
    manager_lines += ["", f"💰 <b>ИТОГО: {money(total_min) if total_min == total_max else f'от {money(total_min)} до {money(total_max)}'} </b>"]
    if data.get("comment"):
        manager_lines += ["", f"💬 <b>Комментарий:</b> {escape(data['comment'])}"]
    manager_text = "\n".join(manager_lines)

    try:
        await callback.bot.send_message(settings.manager_id, manager_text, reply_markup=manager_keyboard(callback.from_user.id, order_id))
    except Exception:
        await callback.message.edit_text(
            "⚠️ Заявка сохранена, но не удалось доставить её менеджеру.\n\n"
            "Проверьте MANAGER_ID в .env и убедитесь, что менеджер запускал этого бота."
        )
        await state.clear()
        return

    await clear_cart(callback.from_user.id)
    await state.clear()
    await callback.message.edit_text(
        f"🎉 <b>Заявка №{order_id} отправлена!</b>\n\n"
        "Спасибо за обращение в Magic Light.\n"
        "Менеджер получил ваш заказ и свяжется с вами для подтверждения деталей.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=(
            ([[InlineKeyboardButton(text="👨‍💼 Связаться с менеджером", url=f"https://t.me/{settings.manager_username}")]] if settings.manager_username else [])
            + [[InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]]
        ))
    )
    await callback.answer("Заявка отправлена ✓")
