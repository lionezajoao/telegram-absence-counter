import sys
from telebot import types

from app.database.bot_db import BotDB

class BotHandler:
    def __init__(self, db_client: BotDB, logger):
        self.db = db_client
        self.logger = logger
        self.user_states = {}
        self.user_data = {}
        self.message_handlers = self._get_message_handlers()
        self.callback_handlers = self._get_callback_handlers()
        self.action_handlers = self._get_action_handlers()
        self.conversation_handlers = self._get_conversation_handlers()
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
            "register_class": self._register_class_command,
            "help": self._help_command,
            "back_to_menu": self._menu_command,
            "skip_semester": self._skip_semester_callback,
        }

    def _get_action_handlers(self):
        return {
            "add_absence": self._add_absence_action,
            "remove_absence": self._remove_absence_action,
            "my_absences": self._my_absences_action,
        }

    def _get_conversation_handlers(self):
        return {
            "AWAITING_CLASS_ID": self._handle_class_id,
            "AWAITING_CLASS_NAME": self._handle_class_name,
            "AWAITING_SEMESTER": self._handle_semester,
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
                return {"type": "send_message", "text": "Ocorreu um erro ao registrar seu chat. Por favor, tente novamente mais tarde."}

        state = self.user_states.get(chat_id)
        if state:
            handler = self.conversation_handlers.get(state)
            if handler:
                return handler(chat_id, text)

        command = text.split(maxsplit=1)[0]
        handler = self.message_handlers.get(command)

        if handler:
            return handler(chat_id, text)
        else:
            self.logger.warning(f"Unrecognized command from chat {chat_id}: '{text}'")
            return {"type": "send_message", "text": "Comando não reconhecido. Digite /help para ver os comandos disponíveis."}

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
                    response = handler(chat_id, action=data)
                    return {"type": "edit_message", "text": response[0], "reply_markup": response[1]}
                elif data == "register_class":
                    return handler(chat_id, call.message.text)
                elif data == "skip_semester":
                    return handler(chat_id)
                else:
                    response = handler(chat_id)
                    if isinstance(response, dict):
                        return response
                    elif isinstance(response, tuple):
                        return {"type": "edit_message", "text": response[0], "reply_markup": response[1]}
                    else:
                        return {"type": "send_message", "text": response}

        return self._create_response_with_menu("Opção não reconhecida.")

    def _create_response_with_menu(self, text):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Menu", callback_data="back_to_menu"))
        return {"type": "send_message", "text": text, "reply_markup": keyboard}

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
        return {"type": "send_message", "text": text, "reply_markup": keyboard}

    def _menu_command(self, chat_id, text=None):
        self.logger.info(f"Handling /menu command for chat {chat_id}.")
        text = "Menu Principal:"
        keyboard = self._create_main_keyboard(chat_id)
        return {"type": "send_message", "text": text, "reply_markup": keyboard}

    def _register_class_command(self, chat_id, text):
        self.logger.info(f"Starting /register_class conversation for chat {chat_id}.")
        self.user_states[chat_id] = "AWAITING_CLASS_ID"
        self.user_data[chat_id] = {}
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Menu", callback_data="back_to_menu"))
        return {"type": "send_message", "text": "Ok, vamos registrar uma nova disciplina. Qual é o ID da disciplina (ex: CS101)?", "reply_markup": keyboard}

    def _handle_class_id(self, chat_id, text):
        self.logger.info(f"Handling class ID for chat {chat_id}: {text}")
        self.user_data[chat_id]["class_id"] = text
        self.user_states[chat_id] = "AWAITING_CLASS_NAME"
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("Menu", callback_data="back_to_menu"))
        return {"type": "send_message", "text": "Qual é o nome da disciplina?", "reply_markup": keyboard}

    def _handle_class_name(self, chat_id, text):
        self.logger.info(f"Handling class name for chat {chat_id}: {text}")
        self.user_data[chat_id]["name"] = text
        self.user_states[chat_id] = "AWAITING_SEMESTER"
        keyboard = types.InlineKeyboardMarkup()
        keyboard.row(
            types.InlineKeyboardButton("Pular", callback_data="skip_semester"),
            types.InlineKeyboardButton("Menu", callback_data="back_to_menu")
        )
        return {"type": "send_message", "text": "Qual é o semestre (opcional)?", "reply_markup": keyboard}

    def _skip_semester_callback(self, chat_id):
        return self._handle_semester(chat_id, "")

    def _handle_semester(self, chat_id, text):
        self.logger.info(f"Handling semester for chat {chat_id}: {text}")
        self.user_data[chat_id]["semester"] = text
        
        class_data = self.user_data[chat_id]
        try:
            self.db.insert_class(chat_id, class_data["class_id"], class_data["name"], class_data["semester"])
            response = f"Disciplina '{class_data['name']}' ({class_data['class_id']}) registrada com sucesso!"
            del self.user_states[chat_id]
            del self.user_data[chat_id]
            return self._create_response_with_menu(response)
        except Exception as e:
            self.logger.error(f"Error registering class: {e}", exc_info=True)
            response = "Erro ao registrar disciplina."
            del self.user_states[chat_id]
            del self.user_data[chat_id]
            return self._create_response_with_menu(response)

    def _add_absence_command(self, chat_id, text):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return self._ask_class_selection(chat_id, action="add_absence")
        class_id = parts[1]
        return self._add_absence_action(chat_id, class_id)

    def _my_absences_command(self, chat_id, text):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return self._ask_class_selection(chat_id, action="my_absences")
        class_id = parts[1]
        return self._my_absences_action(chat_id, class_id)

    def _remove_absence_command(self, chat_id, text):
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            return self._ask_class_selection(chat_id, action="remove_absence")
        class_id = parts[1]
        return self._remove_absence_action(chat_id, class_id)

    def _total_absences_command(self, chat_id, text=None):
        self.logger.info(f"Handling /total_absences command for chat {chat_id}.")
        try:
            total_count = self.db.get_absences_by_class(chat_id)
            if not total_count:
                return self._create_response_with_menu("Nenhuma falta registrada ainda.")
            response = "Faltas por disciplina:\n"
            for row in total_count:
                response += f"- {row['class_name']} ({row['class_id']}): {row['count']} falta(s)\n"
            return self._create_response_with_menu(response)
        except Exception as e:
            self.logger.error(f"Error getting total absences: {e}", exc_info=True)
            return self._create_response_with_menu("Erro ao remover falta.")

    def _list_classes_command(self, chat_id, text=None):
        self.logger.info(f"Handling /list_classes command for chat {chat_id}.")
        try:
            classes = self.db.get_all_classes(chat_id)
            if not classes:
                return self._create_response_with_menu("Nenhuma disciplina registrada ainda. Use /register_class para adicionar uma.")
            response = "Disciplinas registradas:\n"
            for cls in classes:
                response += f"- {cls['name']} ({cls['class_id']})"
                if cls['semester']:
                    response += f" - Semestre: {cls['semester']}"
                response += "\n"
            return self._create_response_with_menu(response)
        except Exception as e:
            self.logger.error(f"Error listing classes: {e}", exc_info=True)
            return self._create_response_with_menu("Erro ao listar disciplinas.")

    def _help_command(self, chat_id, text=None):
        return self._create_response_with_menu((
            "Projeto desenvolvido por https://github.com/lionezajoao:\n"
            "Link do repositório: https://github.com/lionezajoao/telegram-absence-counter\n"
            "Contribuições são bem-vindas!"
        ))

    def _ask_class_selection(self, chat_id, action):
        response_data = {
            "add_absence": "Selecione a disciplina para adicionar falta:",
            "remove_absence": "Selecione a disciplina para remover falta:",
            "my_absences": "Selecione a disciplina para ver suas faltas:"
        }
        title = response_data.get(action, "Selecione uma disciplina:")
        keyboard = self._create_classes_keyboard(chat_id, action)
        return title, keyboard

    def _add_absence_action(self, chat_id, class_id):
        try:
            success = self.db.insert_absence(chat_id, class_id)
            if success:
                count = self.db.get_absence_count(chat_id, class_id)
                return self._create_response_with_menu(f"Falta adicionada para '{class_id}'. Total de faltas: {count}.")
            else:
                return self._create_response_with_menu(f"Erro: Disciplina '{class_id}' não encontrada.")
        except Exception as e:
            self.logger.error(f"Error adding absence: {e}", exc_info=True)
            return self._create_response_with_menu("Erro ao adicionar falta.")

    def _my_absences_action(self, chat_id, class_id):
        try:
            count = self.db.get_absence_count(chat_id, class_id)
            return self._create_response_with_menu(f"Você tem {count} falta(s) em '{class_id}'.")
        except Exception as e:
            self.logger.error(f"Error getting absences: {e}", exc_info=True)
            return self._create_response_with_menu("Erro ao buscar faltas.")

    def _remove_absence_action(self, chat_id, class_id):
        try:
            response = self.db.remove_absence(chat_id, class_id)
            return self._create_response_with_menu(response["message"])
        except Exception as e:
            self.logger.error(f"Error removing absence: {e}", exc_info=True)
            return self._create_response_with_menu("Erro ao remover falta.")
