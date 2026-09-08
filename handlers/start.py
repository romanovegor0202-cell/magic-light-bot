from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from keyboards.main import main_menu
from ui import replace_message

router = Router()

WELCOME = (
    "💍 <b>MAGIC LIGHT</b>\n"
    "<i>Свадебные спецэффекты</i>\n\n"
    "Создаём эффектные моменты, которые становятся частью вашей истории. ✨\n\n"
    "<b>Что хотите сделать?</b>"
)

@router.message(CommandStart())
async def start(message: Message):
    await message.answer(WELCOME, reply_markup=main_menu())

@router.callback_query(F.data == "home")
async def home(callback: CallbackQuery):
    await replace_message(callback.message, WELCOME, reply_markup=main_menu())
    await callback.answer()
