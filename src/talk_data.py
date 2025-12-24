from telegram import Update
from telegram.ext import ContextTypes

from src.constants import CLOSE_BUTTON
from src.utils import send_image, send_text_buttons


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_image(update, context, "talk")
    personalities = {
        "talk_linus_torvalds": "Linus Torvalds (Linux, Git)",
        "talk_guido_van_rossum": "Guido van Rossum (Python)",
        "talk_mark_zuckerberg": "Mark Zuckerberg (Meta, Facebook)",
        **CLOSE_BUTTON,
    }
    await send_text_buttons(update, context, "Choose a personality to chat with ...", personalities)
