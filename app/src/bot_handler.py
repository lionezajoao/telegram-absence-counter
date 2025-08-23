import sys
from telebot import types

from app.database.bot_db import BotDB

class BotHandler:
    def __init__(self, db_client: BotDB, logger):
        self.db = db_client
        self.logger = logger
        self.message_handlers = self._get_message_handlers()
        self.callback_handlers = self._get_callback_handlers()
        self.action_handlers = self._get_action_handlers()
        self.logger.info("BotHandler initialized.")

    def _get_message_handlers(self):
        return {
            "/start": self._start_command,
            "/register_class": self._register_class_command,
            "/add_absence": self._add_absence_command,
            "/my_absences": self._my_absences_command,
            "/remove_absence": self._remove_absence_command,
            "/total_absences": self._total_absences_command,
            "/list_classes": self._list_classes_command,
            "/help": self._help_command,
            "/menu": self._menu_command,
        }

    def _get_callback_handlers(self):
        return {
            "add_absence": self._ask_class_selection,
            "remove_absence": self._ask_class_selection,
            "my_absences": self._ask_class_selection,
            "list_classes": self._list_classes_command,
            "total_absences": self._total_absences_command,
            "register_class": lambda chat_id: "Para registrar uma disciplina, use: /register_class ID_DA_DISCIPLINA | NOME_DA_DISCIPLINA | SEMESTRE (opcional)",
            "help": self._help_command,
            "back_to_menu": self._menu_command,
        }

    def _get_action_handlers(self):
        return {
            "add_absence": self._add_absence_action,
            "remove_absence": self._remove_absence_action,
            "my_absences": self._my_absences_action,
        }

    def handle_message(self, message):
        chat_id = str(message.chat.id)
        username = message.from_user.username
        first_name = message.from_user.first_name
        text = message.text.strip()

        self.logger.info(f"Received message from chat {chat_id} (user: {username or first_name}): '{text}'")

        if not self.db.check_if_chat_exists(chat_id):
            try:
                self.db.insert_chat(chat_id, username, first_name)
                self.logger.info(f"Chat {chat_id} registered successfully.")
            except Exception as e:
                _, _, exc_tb = sys.exc_info()
                self.logger.error(f"Failed to register chat {chat_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
                return "Ocorreu um erro ao registrar seu chat. Por favor, tente novamente mais tarde."

        command = text.split(maxsplit=1)[0]
        handler = self.message_handlers.get(command)

        if handler:
            return handler(chat_id, text)
        else:
            self.logger.warning(f"Unrecognized command from chat {chat_id}: '{text}'")
            return "Comando não reconhecido. Digite /help para ver os comandos disponíveis."

    def handle_callback_query(self, call):
        chat_id = str(call.message.chat.id)
        self.logger.info(f"Handling callback query from chat {chat_id}: {call.data}")

        data = call.data

        if ":" in data:
            action, class_id = data.split(":", 1)
            class_id = class_id.strip()
            handler = self.action_handlers.get(action)
            if handler:
                return handler(chat_id, class_id)
        else:
            handler = self.callback_handlers.get(data)
            if handler:
                if data in ["add_absence", "remove_absence", "my_absences"]:
                    response_data = {
                        "add_absence": "Selecione a disciplina para adicionar falta:",
                        "remove_absence": "Selecione a disciplina para remover falta:",
                        "my_absences": "Selecione a disciplina para ver suas faltas:"
                    }
                    return handler(chat_id, action=data, title=response_data[data])
                else:
                    return handler(chat_id)

        return "Opção não reconhecida. Use /menu para voltar."

    def _create_main_keyboard(self, chat_id):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("Adicionar Falta", callback_data="add_absence"),
            types.InlineKeyboardButton("Remover Falta", callback_data="remove_absence")
        )
        keyboard.row(
            types.InlineKeyboardButton("Minhas Faltas", callback_data="my_absences"),
            types.InlineKeyboardButton("Listar Disciplinas", callback_data="list_classes")
        )
        keyboard.row(
            types.InlineKeyboardButton("Total de Faltas", callback_data="total_absences"),
            types.InlineKeyboardButton("Registrar Disciplina", callback_data="register_class")
        )
        keyboard.row(types.InlineKeyboardButton("Ajuda", callback_data="help"))
        return keyboard

    def _create_classes_keyboard(self, chat_id, action):
        keyboard = types.InlineKeyboardMarkup()
        try:
            classes = self.db.get_all_classes(chat_id)
        except Exception as e:
            self.logger.error(f"Erro ao buscar disciplinas para teclado: {e}", exc_info=True)
            classes = []

        if not classes:
            keyboard.add(types.InlineKeyboardButton("Nenhuma disciplina cadastrada. Use o comando /register_class para cadastrar uma.", callback_data="register_class"))
            keyboard.add(types.InlineKeyboardButton("Voltar ao Menu", callback_data="back_to_menu"))
            return keyboard

        for cls in classes:
            label = f"{cls['name']} ({cls['class_id']})"
            keyboard.add(types.InlineKeyboardButton(label, callback_data=f"{action}:{cls['class_id']}"))

        keyboard.add(types.InlineKeyboardButton("⬅ Voltar", callback_data="back_to_menu"))
        return keyboard

    def _start_command(self, chat_id, text):
        first_name = "user"
        self.logger.info(f"Handling /start command for chat {chat_id}.")
        text = f"Olá, {first_name}! Bem-vindo ao Contador de Faltas. Escolha uma opção abaixo:"
        keyboard = self._create_main_keyboard(chat_id)
        return text, keyboard

    def _menu_command(self, chat_id, text=None):
        self.logger.info(f"Handling /menu command for chat {chat_id}.")
        text = "Menu Principal:"
        keyboard = self._create_main_keyboard(chat_id)
        return text, keyboard

    def _register_class_command(self, chat_id, text):
        self.logger.info(f"Handling /register_class command for chat {chat_id}.")
        text = text.replace("/register_class", "").strip()
        parts = text.split("|")
        if len(parts) < 2:
            return (
                "Uso: /register_class ID_DA_DISCIPLINA | NOME_DA_DISCIPLINA | SEMESTRE (opcional)\n"
                "Exemplo: /register_class mat | Matemática | 2023.1"
            )

        class_id, name, *rest = parts
        semester = rest[0].strip() if rest else None

        try:
            self.db.insert_class(chat_id, class_id.strip(), name.strip(), semester)
            return f"Disciplina '{name.strip()}' ({class_id.strip()}) registrada com sucesso!"
        except Exception as e:
            self.logger.error(f"Error registering class {class_id}: {e}", exc_info=True)
            return "Erro ao registrar disciplina."

    def _add_absence_command(self, chat_id, text):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return self._ask_class_selection(chat_id, action="add_absence", title="Selecione a disciplina para adicionar falta:")
        class_id = parts[1]
        return self._add_absence_action(chat_id, class_id)

    def _my_absences_command(self, chat_id, text):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return self._ask_class_selection(chat_id, action="my_absences", title="Selecione a disciplina para ver suas faltas:")
        class_id = parts[1]
        return self._my_absences_action(chat_id, class_id)

    def _remove_absence_command(self, chat_id, text):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return self._ask_class_selection(chat_id, action="remove_absence", title="Selecione a disciplina para remover falta:")
        class_id = parts[1]
        return self._remove_absence_action(chat_id, class_id)

    def _total_absences_command(self, chat_id, text=None):
        self.logger.info(f"Handling /total_absences command for chat {chat_id}.")
        try:
            total_count = self.db.get_absences_by_class(chat_id)
            if not total_count:
                return "Nenhuma falta registrada ainda."
            response = "Faltas por disciplina:\n"
            for row in total_count:
                response += f"- {row['class_name']} ({row['class_id']}): {row['count']} falta(s)\n"
            return response
        except Exception as e:
            self.logger.error(f"Error getting total absences: {e}", exc_info=True)
            return "Erro ao buscar total de faltas."

    def _list_classes_command(self, chat_id, text=None):
        self.logger.info(f"Handling /list_classes command for chat {chat_id}.")
        try:
            classes = self.db.get_all_classes(chat_id)
            if not classes:
                return "Nenhuma disciplina registrada ainda. Use /register_class para adicionar uma."
            response = "Disciplinas registradas:\n"
            for cls in classes:
                response += f"- {cls['name']} ({cls['class_id']})"
                if cls['semester']:
                    response += f" - Semestre: {cls['semester']}"
                response += "\n"
            return response
        except Exception as e:
            self.logger.error(f"Error listing classes: {e}", exc_info=True)
            return "Erro ao listar disciplinas."

    def _help_command(self, chat_id, text=None):
        return (
            "Comandos disponíveis:\n"
            "/start - Inicia o bot e exibe o menu.\n"
            "/menu - Exibe o menu de opções.\n"
            "/register_class <id> | <nome> | [semestre] - Registra uma nova disciplina.\n"
            "/add_absence <id> - Adiciona uma falta.\n"
            "/remove_absence <id> - Remove uma falta.\n"
            "/my_absences <id> - Verifica suas faltas.\n"
            "/total_absences - Lista o total de faltas por disciplina.\n"
            "/list_classes - Lista todas as disciplinas registradas.\n"
            "/help - Exibe esta mensagem de ajuda.\n"
        )

    def _ask_class_selection(self, chat_id, action, title):
        keyboard = self._create_classes_keyboard(chat_id, action)
        return title, keyboard

    def _add_absence_action(self, chat_id, class_id):
        try:
            success = self.db.insert_absence(chat_id, class_id)
            if success:
                count = self.db.get_absence_count(chat_id, class_id)
                return f"Falta adicionada para '{class_id}'. Total de faltas: {count}.\nUse /menu para voltar."
            else:
                return f"Erro: Disciplina '{class_id}' não encontrada."
        except Exception as e:
            self.logger.error(f"Error adding absence: {e}", exc_info=True)
            return "Erro ao adicionar falta."

    def _my_absences_action(self, chat_id, class_id):
        try:
            count = self.db.get_absence_count(chat_id, class_id)
            return f"Você tem {count} falta(s) em '{class_id}'.\nUse /menu para voltar."
        except Exception as e:
            self.logger.error(f"Error getting absences: {e}", exc_info=True)
            return "Erro ao buscar faltas."

    def _remove_absence_action(self, chat_id, class_id):
        try:
            response = self.db.remove_absence(chat_id, class_id)
            return response["message"] + "\nUse /menu para voltar."
        except Exception as e:
            self.logger.error(f"Error removing absence: {e}", exc_info=True)
            return "Erro ao remover falta."
