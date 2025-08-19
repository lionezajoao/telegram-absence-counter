import os
import telebot
from dotenv import load_dotenv

from app.src.bot_handler import BotHandler
from app.database.bot_db import BotDB
from app.src.config import get_logger

load_dotenv()

if __name__ == "__main__":
    # Configure logging
    logger = get_logger(__name__)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(log_level)

    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.critical("BOT_TOKEN environment variable not set. Exiting.")
        raise ValueError("BOT_TOKEN environment variable not set.")

    bot = telebot.TeleBot(BOT_TOKEN)

    db_client = BotDB(logger)
    bot_handler = BotHandler(db_client, logger)

    logger.info("Bot is starting...")

    @bot.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        try:
            response_text = bot_handler.handle_message(message)
            bot.reply_to(message, response_text)
        except Exception as e:
            logger.exception(f"Error handling message from chat {message.chat.id}: {e}")
            bot.reply_to(message, "Ocorreu um erro inesperado. Por favor, tente novamente mais tarde.")

    try:
        bot.polling(none_stop=True)
    except Exception as e:
        logger.critical(f"Bot polling failed: {e}", exc_info=True)
    finally:
        logger.info("Bot is shutting down. Closing database connection.")
        db_client.close()
