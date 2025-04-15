import os
import telebot
from dotenv import load_dotenv

from app.src.bot_handler import BotHandler

load_dotenv()

if __name__ == "__main__":
    
    bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
    handler = BotHandler()
    print("Bot is running...")

    @bot.message_handler(commands=['start'])
    def start(message):
        bot.send_message(message.chat.id, "Olá! Bem vindo ao ContaFalta, um bot para controle de faltas. Digite /help para ver os comandos disponíveis.")
        handler.insert_new_chat(message.chat.id, message.chat.username, message.chat.first_name)

    @bot.message_handler(commands=['help'])
    def help_command(message):
        bot.send_message(message.chat.id, "Comandos disponíveis:\n /start - Inicia o bot\n /help - Mostra os comandos disponíveis\n /addclass - Adiciona uma nova turma\n /addchat - Adiciona um novo chat\n /removeclass - Remove uma turma\n /removechat - Remove um chat")
    
    @bot.message_handler(func=lambda message: True)
    def echo_all(message):
        bot.reply_to(message, message.text)

    bot.polling(none_stop=True)
