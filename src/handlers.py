import logging
from random import choice

from telegram import Update
from telegram.ext import ContextTypes

from config import CHATGPT_TOKEN
from gpt import ChatGPTService
from utils import (send_image, send_text, load_message, show_main_menu, load_prompt, send_text_buttons)

chatgpt_service = ChatGPTService(CHATGPT_TOKEN)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
            "start": "Main menu",
            "random": "Get a random fact",
            "gpt": "Ask ChatGPT",
            "talk": "Talk with a famous person",
            "quiz": "Test your knowledge"
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
            "random": "Want another fact",
            "start": "Close"
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
    if data == "random":
        await random(update, context)
    elif data == "start":
        await start(update, context)

async def gpt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_image(update, context, "gpt")
    chatgpt_service.set_prompt(load_prompt("gpt"))
    await send_text(update, context, "Ask me a question ...")
    context.user_data["conversation_state"] = "gpt"


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    conversation_state = context.user_data.get("conversation_state")
    if conversation_state == "gpt":
        waiting_message = await send_text(update, context, "...")
        try:
            response = await chatgpt_service.add_message(message_text)
            await send_text(update, context, response)
        except Exception as e:
            logger.error(f"An error occurred while receiving a response from ChatGPT: {e}")
            await send_text(update, context, "An error occurred while processing your message.")
        finally:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=waiting_message.message_id
            )
    if conversation_state == "talk":
        personality = context.user_data.get("selected_personality")
        if personality:
            prompt = load_prompt(personality)
            chatgpt_service.set_prompt(prompt)
        else:
            await send_text(update, context, "Please choose a personality to start the conversation!")
            return
        waiting_message = await send_text(update, context, "...")
        try:
            response = await chatgpt_service.add_message(message_text)
            buttons = {"start": "Close"}
            personality_name = personality.replace("talk_", "").replace("_", " ").title()
            await send_text_buttons(update, context, f"{personality_name}: {response}", buttons)
        except Exception as e:
            logger.error(f"An error occurred while receiving a response from ChatGPT: {e}")
            await send_text(update, context, "An error occurred while processing your message.")
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=waiting_message.message_id)
        finally:
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=waiting_message.message_id
            )
    if not conversation_state:
        intent_recognized = await inter_random_input(update, context, message_text)
        if not intent_recognized:
            await show_funny_response(update, context)
        return


async def talk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await send_image(update, context, "talk")
    personalities = {
        "talk_linus_torvalds": "Linus Torvalds (Linux, Git)",
        "talk_guido_van_rossum": "Guido van Rossum (Python)",
        "talk_mark_zuckerberg": "Mark Zuckerberg (Meta, Facebook)",
        "start": "Close",
    }
    await send_text_buttons(update, context, "Choose a personality to chat with ...", personalities)


async def talk_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "start":
        context.user_data.pop("conversation_state", None)
        context.user_data.pop("selected_personality", None)
        await start(update, context)
        return
    if data.startswith("talk_"):
        context.user_data.clear()
        context.user_data["selected_personality"] = data
        context.user_data["conversation_state"] = "talk"
        prompt = load_prompt(data)
        chatgpt_service.set_prompt(prompt)
        personality_name = data.replace("talk_", "").replace("_", " ").title()
        await send_image(update, context, data)
        buttons = {"start": "CLose"}
        await send_text_buttons(
            update,
            context,
            f"Hello, I`m {personality_name}."
            f"\nI heard you wanted to ask me something. "
            f"\nYou can ask questions in your native language.",
            buttons
        )


async def inter_random_input(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text):
    message_text_lower = message_text.lower()
    if any(keyword in message_text_lower for keyword in ["fact", "interesting", "random"]):
        await send_text(
            update,
            context,
            text="It looks like you’re interested in random facts! I’ll show you one now..."
        )
        await random(update, context)
        return True

    elif any(keyword in message_text_lower for keyword in ["gpt", "chat", "question", "ask", "find out"]):
        await send_text(
            update,
            context,
            text="It looks like you have a question! Switching to ChatGPT conversation mode..."
        )
        await gpt(update, context)
        return True

    elif any(keyword in message_text_lower for keyword in ["conversation", "talk", "communicate", "personality"]):
        await send_text(
            update,
            context,
            text="It looks like you want to chat with a famous personality! Here are the available options..."
        )
        await talk(update, context)
        return True
    return False


async def show_funny_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    funny_responses = [
        "Hmm… interesting, but I didn’t understand what you want. Maybe try one of the menu commands?",
        "That’s a very interesting message! But I need clearer instructions. Here are the available commands:",
        "Oh! Looks like you caught me off guard! I can do a lot, but I need a specific command:",
        "Sorry, my algorithms didn’t recognize this as a command. Here’s what I can do for sure:",
        "This message is as mysterious as a unicorn in the wild! Try one of these commands:",
        "I’m trying to understand your message… but it’s better to use one of the commands:",
        "Oh! A random message! I can be random too, but it’s better to use commands:",
        "Hmm, that didn’t work. Maybe let’s try these commands?",
        "This message is as beautiful as a rainbow! But for a proper interaction, try:",
        "According to my calculations, this message doesn’t match any of my commands. Here they are:",
    ]
    random_response = choice(funny_responses)
    available_commands = """
    - Not sure what to choose? Start with /start,
    - Try the /gpt command to ask a question,
    """
    full_message = f"{random_response}\n{available_commands}"
    await update.message.reply_text(full_message)