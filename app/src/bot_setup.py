import os
import telebot
from dotenv import load_dotenv

from app.src.config import get_logger
from app.src.bot_handler import BotHandler

load_dotenv()

logger = get_logger(__name__)

def initialize_bot(logger):
    """Initializes and returns the TeleBot instance."""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN environment variable not set. Exiting.")
        raise ValueError("BOT_TOKEN environment variable not set.")
    return telebot.TeleBot(BOT_TOKEN)

def setup_handlers(bot: telebot.TeleBot, bot_handler: BotHandler, logger):
    """Sets up the message and callback query handlers for the bot."""
    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        try:
            response = bot_handler.handle_message(message)
            if response:
                if response.get("type") == "send_message":
                    bot.reply_to(message, response["text"], reply_markup=response.get("reply_markup"))
        except Exception as e:
            logger.exception(f"Error handling message from chat {message.chat.id}: {e}")
            bot.reply_to(message, "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde.")

    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback_queries(call):
        try:
            response = bot_handler.handle_callback_query(call)
            bot.answer_callback_query(call.id)
            if response:
                if response.get("type") == "send_message":
                    bot.send_message(call.message.chat.id, response["text"], reply_markup=response.get("reply_markup"))
                elif response.get("type") == "edit_message":
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=response["text"], reply_markup=response.get("reply_markup"))
        except Exception as e:
            logger.exception(f"Error handling callback query from chat {call.message.chat.id}: {e}")
            bot.send_message(call.message.chat.id, "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde.")

def start_polling(bot: telebot.TeleBot, logger):
    """Starts the bot's polling loop."""
    logger.info("Bot is starting...")
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.critical(f"Bot polling failed: {e}", exc_info=True)
        raise e
