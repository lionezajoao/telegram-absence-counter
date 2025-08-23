import os
import telebot
from dotenv import load_dotenv

from app.database.bot_db import BotDB
from app.src.bot_handler import BotHandler
from app.src.bot_setup import initialize_bot, setup_handlers, start_polling, logger

if __name__ == "__main__":
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logger.setLevel(log_level)

    db_client = None
    try:
        bot = initialize_bot(logger)
        db_client = BotDB(logger)
        bot_handler = BotHandler(db_client, logger)

        bot.set_my_commands([
            telebot.types.BotCommand(command="/start", description="Iniciar o bot"),
            telebot.types.BotCommand(command="/add_absence", description="Adicionar uma falta"),
            telebot.types.BotCommand(command="/remove_absence", description="Remover uma falta"),
            telebot.types.BotCommand(command="/my_absences", description="Ver minhas faltas"),
            telebot.types.BotCommand(command="/list_classes", description="Listar disciplinas"),
            telebot.types.BotCommand(command="/total_absences", description="Ver total de faltas"),
            telebot.types.BotCommand(command="/register_class", description="Registrar uma nova disciplina"),
            telebot.types.BotCommand(command="/help", description="Obter ajuda sobre os comandos disponíveis"),
            telebot.types.BotCommand(command="/menu", description="Exibe o menu de opções")
        ])

        setup_handlers(bot, bot_handler, logger)
        start_polling(bot, logger)

    except ValueError as e:
        logger.critical(str(e))
    except Exception as e:
        logger.critical(f"An unexpected error occurred: {e}", exc_info=True)
    finally:
        if db_client:
            logger.info("Bot is shutting down. Closing database connection.")
            db_client.close_connection()