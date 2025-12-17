import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import CHATGPT_TOKEN
from gpt import ChatGPTService
from utils import (send_image, send_text, load_message, show_main_menu, load_prompt, send_text_buttons)

chatgpt_service = ChatGPTService(CHATGPT_TOKEN)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, "start")
    await send_text(update, context, load_message("start"))
    await show_main_menu(
        update,
        context,
        {
            'start': 'Main menu',
            'random': 'Get a random fact',
            'gpt': 'Ask ChatGPT',
            'talk': 'Talk with a famous person',
            'quiz': 'Test your knowledge'
        }
    )


async def random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_image(update, context, "random")
    message_to_delete = await send_text(update, context, "Looking for random fact...")
    try:
        prompt = load_prompt("random")
        fact = await chatgpt_service.send_question(
            prompt_text=prompt,
            message_text="Tell me a random fact"
        )
        buttons = {
            'random': 'Want another fact',
            'start': 'Close'
        }
        await send_text_buttons(update, context, fact, buttons)
    except Exception as e:
        logger.error(f"An error occurred in the handler /random: {e}")
        await send_text(update, context, "An error occurred while getting a random fact.")
    finally:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=message_to_delete.message_id
        )


async def random_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == 'random':
        await random(update, context)
    elif data == 'start':
        await start(update, context)