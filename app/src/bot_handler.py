from app.database.bot_db import BotDB
import sys

class BotHandler:
    def __init__(self, db_client: BotDB, logger):
        self.db = db_client
        self.logger = logger
        self.logger.info("BotHandler initialized.")

    def handle_message(self, message):
        chat_id = str(message.chat.id)
        username = message.from_user.username
        first_name = message.from_user.first_name
        text = message.text.strip()

        self.logger.info(f"Received message from chat {chat_id} (user: {username or first_name}): '{text}'")

        # Ensure chat is registered
        if not self.db.check_if_chat_exists(chat_id):
            try:
                self.db.insert_chat(chat_id, username, first_name)
                self.logger.info(f"Chat {chat_id} registered successfully.")
            except Exception as e:
                _, _, exc_tb = sys.exc_info()
                self.logger.error(f"Failed to register chat {chat_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
                return "Ocorreu um erro ao registrar seu chat. Por favor, tente novamente mais tarde."

        if text == "/start":
            return self._start_command(chat_id, first_name)
        elif text.startswith("/register_class"):
            return self._register_class_command(chat_id, text)
        elif text.startswith("/add_absence"):
            return self._add_absence_command(chat_id, text)
        elif text.startswith("/my_absences"):
            return self._my_absences_command(chat_id, text)
        elif text == "/total_absences":
            return self._total_absences_command(chat_id)
        elif text == "/list_classes":
            return self._list_classes_command(chat_id)
        elif text == "/help":
            return self._help_command()
        else:
            self.logger.warning(f"Unrecognized command from chat {chat_id}: '{text}'")
            return "Comando não reconhecido. Digite /help para ver os comandos disponíveis."

    def _start_command(self, chat_id, first_name):
        self.logger.info(f"Handling /start command for chat {chat_id}.")
        return f"Olá, {first_name}! Bem-vindo ao Contador de Faltas. Digite /help para ver os comandos disponíveis."

    def _register_class_command(self, chat_id, text):
        self.logger.info(f"Handling /register_class command for chat {chat_id}.")
        text = text.replace("/register_class", "")
        parts = text.split("|")
        if len(parts) < 3:
            self.logger.warning(f"Invalid /register_class usage by chat {chat_id}: '{text}'")
            return "Uso: /register_class <id_disciplina> | <nome_disciplina> | [semestre]"

        class_id = parts[0].strip()
        name = parts[1].strip()
        semester = str(parts[2]).strip() if len(parts) > 2 else None

        self.logger.info(f"Parsed /register_class command for chat {chat_id}: {class_id}, {name}, {semester}")

        try:
            self.db.insert_class(chat_id, class_id, name, semester)
            self.logger.info(f"Class '{name}' ({class_id}) registered by chat {chat_id}.")
            return f"Disciplina '{name}' ({class_id}) registrada com sucesso!"
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            self.logger.error(f"Error registering class {class_id} for chat {chat_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            return f"Erro ao registrar disciplina: {e}"

    def _add_absence_command(self, chat_id, text):
        self.logger.info(f"Handling /add_absence command for chat {chat_id}.")
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            self.logger.warning(f"Invalid /add_absence usage by chat {chat_id}: '{text}'")
            return "Uso: /add_absence <id_disciplina>"
        
        class_id = parts[1]

        try:
            success = self.db.insert_absence(chat_id, class_id)
            if success:
                count = self.db.get_absence_count(chat_id, class_id)
                self.logger.info(f"Absence added for chat {chat_id} in class {class_id}. New count: {count}.")
                return f"Falta adicionada para '{class_id}'. Total de faltas: {count}."
            else:
                self.logger.info(f"Attempted to add absence for non-existent class '{class_id}' by chat {chat_id}.")
                return f"Erro: Disciplina '{class_id}' não encontrada. Registre-a primeiro com /register_class."
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            self.logger.error(f"Error adding absence for chat {chat_id}, class {class_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            return f"Erro ao adicionar falta: {e}"

    def _my_absences_command(self, chat_id, text):
        self.logger.info(f"Handling /my_absences command for chat {chat_id}.")
        parts = text.split(maxsplit=1)
        if len(parts) < 2:
            self.logger.warning(f"Invalid /my_absences usage by chat {chat_id}: '{text}'")
            return "Uso: /my_absences <id_disciplina>"
        
        class_id = parts[1]
        try:
            count = self.db.get_absence_count(chat_id, class_id)
            if count > 0:
                self.logger.info(f"Retrieved {count} absences for chat {chat_id} in class {class_id}.")
                return f"Você tem {count} falta(s) em '{class_id}'."
            else:
                self.logger.info(f"No absences found for chat {chat_id} in class {class_id}.")
                return f"Você não tem faltas registradas em '{class_id}' ou a disciplina não existe."
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            self.logger.error(f"Error getting absences for chat {chat_id}, class {class_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            return f"Erro ao buscar faltas: {e}"

    def _total_absences_command(self, chat_id):
        self.logger.info(f"Handling /total_absences command for chat {chat_id}.")
        try:
            total_count = self.db.get_total_absences(chat_id)
            self.logger.info(f"Retrieved total {total_count} absences for chat {chat_id}.")
            return f"Você tem um total de {total_count} falta(s) em todas as disciplinas."
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            self.logger.error(f"Error getting total absences for chat {chat_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            return f"Erro ao buscar total de faltas: {e}"

    def _list_classes_command(self, chat_id):
        self.logger.info(f"Handling /list_classes command for chat {chat_id}.")
        try:
            classes = self.db.get_all_classes(chat_id)
            if not classes:
                self.logger.info(f"No classes registered for chat {chat_id}.")
                return "Nenhuma disciplina registrada ainda. Use /register_class para adicionar uma."
            
            response = "Disciplinas registradas:\n"
            for cls in classes:
                response += f"- {cls['name']} ({cls['class_id']})"
                if cls['semester']:
                    response += f" - Semestre: {cls['semester']}"
                response += "\n"
            self.logger.info(f"Listed {len(classes)} classes for chat {chat_id}.")
            return response
        except Exception as e:
            _, _, exc_tb = sys.exc_info()
            self.logger.error(f"Error listing classes for chat {chat_id} on line {exc_tb.tb_lineno}: {e}", exc_info=True)
            return f"Erro ao listar disciplinas: {e}"

    def _help_command(self):
        self.logger.info("Handling /help command.")
        return (
            "Comandos disponíveis:\n"
            "/start - Inicia o bot e exibe mensagem de boas-vindas.\n"
            "/register_class <id> | <nome> | [semestre] - Registra uma nova disciplina. Lembre-se de separar os campos com o caractere '|'.\n"
            "/add_absence <id_disciplina> - Adiciona uma falta para a disciplina especificada.\n"
            "/my_absences <id_disciplina> - Verifica suas faltas para a disciplina especificada.\n"
            "/total_absences - Verifica o total de faltas em todas as disciplinas.\n"
            "/list_classes - Lista todas as disciplinas registradas.\n"
            "/help - Exibe esta mensagem de ajuda.\n"
        )