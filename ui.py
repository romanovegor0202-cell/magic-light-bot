async def replace_message(message, text: str, reply_markup=None):
    """Replace a bot message whether it is a text message or a photo message."""
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer(text, reply_markup=reply_markup)
